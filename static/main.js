let wavesurfer;       // The main WaveSurfer instance
let audioReady = false; // Flag to track whether audio is loaded

function openTab(evt, tabName) {
    var i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";

    // Dynamically load the content
    fetchContent(tabName).then(() => {
        attachFormHandler(tabName);
        if (tabName === 'Slice') {
            initializeWaveform();
        } else if (tabName === 'DrumRackInspector') {
            initializeDrumRackWaveforms();
        }
    });
}

async function fetchContent(tabName) {
    try {
        // Convert tab name to URL format (lowercase and preserve hyphens)
        const urlPath = tabName.replace(/([A-Z])/g, '-$1')  // Add hyphens before capitals
            .toLowerCase()  // Convert to lowercase
            .replace(/^-/, '');  // Remove leading hyphen if present
        const response = await fetch(`/${urlPath}`);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.text();
        document.getElementById(tabName).innerHTML = data;
    } catch (error) {
        document.getElementById(tabName).innerHTML = `<p style="color: red;">Error loading content: ${error}</p>`;
    }
}

function attachFormHandler(tabName) {
    const form = document.querySelector(`#${tabName} form`);
    if (!form) return;

    // For DrumRackInspector, use change event on select
    if (tabName === 'DrumRackInspector') {
        const select = form.querySelector('select');
        if (select) {
            select.addEventListener('change', async function(event) {
                event.preventDefault();
                await submitForm(form, tabName);
            });
        }
    } else {
        // For other forms, use submit event
        form.addEventListener('submit', async function(event) {
            event.preventDefault();
            await submitForm(form, tabName);
        });
    }
}

async function submitForm(form, tabName) {
    const formData = new FormData(form);
    const selectedValue = form.querySelector('select')?.value; // Store selected value

    // Collect regions data from WaveSurfer if in Slice tab
    if (tabName === 'Slice' && wavesurfer) {
        const regionsArray = Object.values(wavesurfer.regions.list).map(region => ({ start: region.start, end: region.end }));
        formData.append('regions', JSON.stringify(regionsArray));
    }

    const url = `/${tabName.replace(/([A-Z])/g, '-$1')
        .toLowerCase()
        .replace(/^-/, '')}`;
    const method = form.method.toUpperCase();

    try {
        const response = await fetch(url, {
            method: method,
            body: formData
        });

        // Check if the response is an attachment
        const contentDisposition = response.headers.get('Content-Disposition');
        if (contentDisposition && contentDisposition.includes('attachment')) {
            const blob = await response.blob();
            const urlBlob = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = urlBlob;
            const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
            const filename = filenameMatch ? filenameMatch[1] : 'download.zip';
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(urlBlob);
        } else {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const result = await response.text();
            document.getElementById(tabName).innerHTML = result;

            // Re-attach the form handler in case of multiple submissions
            attachFormHandler(tabName);

            // Restore selected value if it exists
            if (selectedValue) {
                const select = document.querySelector(`#${tabName} select`);
                if (select) {
                    select.value = selectedValue;
                }
            }

            if (tabName === 'Slice') {
                initializeWaveform();
            } else if (tabName === 'DrumRackInspector') {
                initializeDrumRackWaveforms();
            }
        }
    } catch (error) {
        document.getElementById(tabName).innerHTML = `<p style="color: red;">Error submitting form: ${error}</p>`;
    }
}

/**
 * Initialize waveforms for drum rack samples
 */
// Keep track of all drum rack waveform instances
let drumRackWaveforms = [];

function initializeDrumRackWaveforms() {
    // Clear previous instances
    drumRackWaveforms.forEach(ws => {
        try {
            ws.destroy();
        } catch (e) {
            console.error('Error destroying wavesurfer instance:', e);
        }
    });
    drumRackWaveforms = [];

    const containers = document.querySelectorAll('.waveform-container');
    containers.forEach(container => {
        const audioPath = container.getAttribute('data-audio-path');
        if (!audioPath) return;
        
        const wavesurfer = WaveSurfer.create({
            container: container,
            waveColor: 'violet',
            progressColor: 'purple',
            height: 64,
            responsive: true,
            normalize: true,
            minPxPerSec: 50,
            barWidth: 2,
            interact: false, // Disable seeking
            hideScrollbar: true // Hide the scrollbar
        });
        
        // Store wavesurfer instance in container for easy access
        container.wavesurfer = wavesurfer;
        drumRackWaveforms.push(wavesurfer);
        
        // Load the audio file
        wavesurfer.load(audioPath);
        
        // Handle finish event to reset state
        wavesurfer.on('finish', () => {
            wavesurfer.stop();
        });
        
        // Handle click event
        container.addEventListener('click', () => {
            // Stop all waveforms first
            drumRackWaveforms.forEach(ws => {
                if (ws.isPlaying()) {
                    ws.stop();
                }
            });
            
            // Always start from beginning
            wavesurfer.stop();
            wavesurfer.seekTo(0);
            requestAnimationFrame(() => wavesurfer.play(0));
        });
    });
}

/**
 * Initialize (or reuse) the WaveSurfer instance when "Slice" tab is opened.
 */
function initializeWaveform() {
    const waveform = document.getElementById('waveform');
    
    // If there's a placeholder and no existing WaveSurfer instance, create it
    if (waveform && !waveform.waveSurferInstance) {
        wavesurfer = WaveSurfer.create({
            container: '#waveform',
            waveColor: 'violet',
            progressColor: 'purple',
            height: 128,
            responsive: true,
            plugins: [WaveSurfer.regions.create({})]
        });

        // Set flag and create initial contiguous slices when audio is loaded
        wavesurfer.on('ready', () => {
            if (wavesurfer.getDuration() > 0) {
                audioReady = true;
                createContiguousRegions();
                addResetSlicesButton();
            } else {
                audioReady = false;
            }
        });

        // Listen for region clicks to play just that slice
        wavesurfer.on('region-click', (region, e) => {
            e.stopPropagation(); 
            region.play();
        });

        // Whenever the user finishes resizing a region,
        // force them to remain contiguous (no overlap/gap).
        wavesurfer.on('region-update-end', keepRegionsContiguous);
    }

    // Listen for changes in num_slices input to recalc slices
    const numSlicesInput = document.getElementById('num_slices');
    if (numSlicesInput) {
        numSlicesInput.addEventListener('change', function() {
            if (audioReady) {
                wavesurfer.stop();       // Stop playback if audio is playing
                wavesurfer.clearRegions(); 
                createContiguousRegions(); 
            }
        });
    }

    // Listen for a new file selection
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                // Clear old regions, reset flag, and load new file
                wavesurfer.clearRegions();
                audioReady = false;
                wavesurfer.loadBlob(file);
            }
        });
    }
}

/**
 * Create and append the "Reset Slices" button below the waveform.
 */
function addResetSlicesButton() {
    const waveform = document.getElementById('waveform');
    if (!waveform) return;

    // Check if the button already exists
    if (document.getElementById('reset-slices')) return;

    // Only add button if audio is loaded
    if (wavesurfer.getDuration() <= 0) return;

    const resetButton = document.createElement('button');
    resetButton.id = 'reset-slices';
    resetButton.innerText = 'Reset Slices';

    resetButton.addEventListener('click', () => {
        recalcSlices();
    });

    waveform.parentNode.appendChild(resetButton);
}

/**
 * Create contiguous slices based on the first and last regions' start and end points.
 * If no regions exist, use the full duration of the audio.
 */
function createContiguousRegions() {
    const numSlicesInput = document.getElementById('num_slices');
    if (!numSlicesInput) return;

    const numSlices = parseInt(numSlicesInput.value, 10) || 0;
    if (!audioReady || !wavesurfer || numSlices <= 0) return;

    let slicingStart = 0;
    let slicingEnd = wavesurfer.getDuration();

    const regions = Object.values(wavesurfer.regions.list)
        .sort((a, b) => a.start - b.start);

    if (regions.length > 0) {
        slicingStart = regions[0].start;
        slicingEnd = regions[regions.length - 1].end;
    }

    const slicingDuration = slicingEnd - slicingStart;
    const sliceDuration = slicingDuration / numSlices;

    for (let i = 0; i < numSlices; i++) {
        let regionOptions = {
            start: slicingStart + i * sliceDuration,
            end: slicingStart + (i + 1) * sliceDuration,
            color: 'rgba(0, 255, 0, 0.2)',
            drag: false  // let users resize edges, but not move the entire slice
            // omit "resize: false" so edges are resizable
        };

        // Allow the first region to resize its start
        if (i === 0) {
            regionOptions.resize = 'left';
        }

        // Allow the last region to resize its end
        if (i === numSlices - 1) {
            regionOptions.resize = 'right';
        }

        wavesurfer.addRegion(regionOptions);
    }
}

/**
 * Ensure all regions remain contiguous after resizing:
 * - The end of one region is the start of the next.
 * - The first region can start after 0 if adjusted.
 * - The last region ends at the full duration.
 */
function keepRegionsContiguous(updatedRegion) {
    // Get all regions, sorted by start time
    const regions = Object.values(wavesurfer.regions.list)
        .sort((a, b) => a.start - b.start);

    // Find which region was just updated
    const idx = regions.findIndex(r => r.id === updatedRegion.id);
    if (idx === -1) return;

    const duration = wavesurfer.getDuration();

    // Clamp the updated region within [0, duration]
    if (updatedRegion.start < 0) {
        updatedRegion.update({ start: 0 });
    }
    if (updatedRegion.end > duration) {
        updatedRegion.update({ end: duration });
    }

    if (idx > 0) {
        // If not the first region, snap its start to the end of the previous region
        const prev = regions[idx - 1];
        prev.update({ end: updatedRegion.start });
    }

    if (idx < regions.length - 1) {
        // If not the last region, snap its end to the start of the next region
        const next = regions[idx + 1];
        next.update({ start: updatedRegion.end });
    }
}

// Recalculate slices if needed (this is left for legacy calls in your code)
function recalcSlices() {
    if (!audioReady || !wavesurfer) return;
    wavesurfer.stop();
    wavesurfer.clearRegions();
    createContiguousRegions();
}

// Open the default tab when the page loads
window.onload = function() {
    document.getElementById("defaultOpen").click();
}

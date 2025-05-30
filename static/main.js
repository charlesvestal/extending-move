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
            // Ensure the modal’s open/close handlers get bound on first load
            if (typeof initializeTimeStretchModal === 'function') {
                initializeTimeStretchModal();
            }
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
        
        // Find and re-run any scripts in the loaded content
        const scripts = document.getElementById(tabName).querySelectorAll("script");
        scripts.forEach(oldScript => {
            const newScript = document.createElement("script");
            if (oldScript.src) {
                newScript.src = oldScript.src;
            } else {
                newScript.textContent = oldScript.textContent;
            }
            document.body.appendChild(newScript);
        });
        
        if (tabName === 'Chord' && typeof initChordTab === 'function') {
            initChordTab();
        }
    } catch (error) {
        document.getElementById(tabName).innerHTML = `<p style="color: red;">Error loading content: ${error}</p>`;
    }
}

function initializeRestoreForm() {
    const select = document.querySelector('select[name="mset_index"]');
    if (select && select.options.length > 0 && !select.value) {
        select.selectedIndex = 0;
    }
}

async function handleRestoreSubmit(form) {
    const formData = new FormData(form);
    try {
        const response = await fetch("/restore", {
            method: "POST",
            body: formData
        });
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const contentType = response.headers.get('Content-Type') || '';
        if (contentType.includes('application/json')) {
            // Handle JSON response for both success and error
            const data = await response.json();
            const resultMessage = document.getElementById("result-message");
            if (resultMessage) {
                resultMessage.innerHTML = data.message;
            }
            // Update pad dropdown options if provided
            if (data.options) {
                const select = document.querySelector('#Restore select[name="mset_index"]');
                if (select) {
                    select.innerHTML = data.options;
                    select.selectedIndex = 0;
                }
            }
        } else {
            // Replace the entire Restore tab content on HTML response
            const html = await response.text();
            const container = document.getElementById("Restore");
            if (container) {
                container.innerHTML = html;
                initializeRestoreForm();
                attachFormHandler('Restore');
            }
        }
    } catch (error) {
        const resultMessage = document.getElementById("result-message");
        if (resultMessage) {
            resultMessage.innerHTML = `Error: ${error.message}`;
        }
    }
}

function attachFormHandler(tabName) {
    console.log("Attaching form handlers for tab:", tabName);
    // Special case: intercept both Create and Generate forms in Set Management tab
    if (tabName === 'SetManagement') {
      const container = document.getElementById(tabName);
      if (container) {
        // Attach to all forms in the SetManagement container
        container.querySelectorAll('form').forEach(form => {
          form.addEventListener('submit', async function(event) {
            event.preventDefault();
            await submitForm(form, tabName);
          });
        });
      }
      return;
    }

    const form = document.querySelector(`#${tabName} form`);
    if (!form) return;

    // Handle transient_detect checkbox/hidden sync for Slice tab
    if (tabName === 'Slice') {
        const transientCheckbox = form.querySelector('#transient_detect');
        const transientHidden = form.querySelector('#transient_detect_hidden');
        if (transientCheckbox && transientHidden) {
            transientCheckbox.addEventListener('change', function() {
                transientHidden.value = this.checked ? "1" : "0";
            });
            // Set initial state
            transientHidden.value = transientCheckbox.checked ? "1" : "0";
        }

        // Attach Detect Transients button handler
        const detectBtn = form.querySelector('#detect-transients-btn');
        if (detectBtn) {
            detectBtn.addEventListener('click', async function() {
                const fileInput = form.querySelector('#file');
                const msg = document.getElementById('transient-detect-message');
                if (!fileInput || !fileInput.files[0]) {
                    msg.textContent = "Please select a file first.";
                    msg.style.color = "orange";
                    return;
                }
                msg.textContent = "Detecting transients...";
                msg.style.color = "#337ab7";
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                // --- Add sensitivity slider support ---
                const sensInput = form.querySelector('#sensitivity');
                const sensitivity = sensInput ? sensInput.value : 0.07;
                formData.append('sensitivity', sensitivity);
                // --- End sensitivity slider support ---
                try {
                    const response = await fetch('/detect-transients', {
                        method: 'POST',
                        body: formData
                    });
                    const data = await response.json();
                    if (data.success && data.regions) {
                        msg.textContent = data.message;
                        msg.style.color = "green";
                        // Update regions on waveform
                        if (typeof wavesurfer !== "undefined" && wavesurfer) {
                            wavesurfer.clearRegions();
                            data.regions.forEach(r => {
                                wavesurfer.addRegion({
                                    start: r.start,
                                    end: r.end,
                                    color: 'rgba(0, 255, 0, 0.2)',
                                    drag: false
                                });
                            });
                        }
                    } else {
                        msg.textContent = data.message || "No transients detected.";
                        msg.style.color = "orange";
                    }
                } catch (err) {
                    msg.textContent = "Error detecting transients.";
                    msg.style.color = "red";
                    console.error(err);
                }
            });
        }

        // --- Sensitivity slider live update ---
        const sensSlider = form.querySelector('#sensitivity');
        const sensValue = document.getElementById('sensitivity-value');
        if (sensSlider && sensValue) {
            sensSlider.addEventListener('input', function() {
                sensValue.textContent = sensSlider.value;
            });
        }
    }

    // Initialize restore form if applicable
    if (tabName === 'Restore') {
        initializeRestoreForm();
    }

    // For DrumRackInspector
    if (tabName === 'DrumRackInspector') {
        // Handle preset selection change
        const select = form.querySelector('select');
        if (select) {
            select.addEventListener('change', async function(event) {
                event.preventDefault();
                await submitForm(form, tabName);
            });
        }
        
        // Handle all forms in the drum grid (for reverse buttons)
        const drumGrid = document.querySelector('.drum-grid');
        if (drumGrid) {
            drumGrid.addEventListener('submit', async function(event) {
                if (event.target.matches('form')) {
                    event.preventDefault();
                    await submitForm(event.target, tabName);
                }
            });
        }
    } 
    // For SynthPresetInspector
    else if (tabName === 'SynthPresetInspector') {
        // Handle preset selection change
        const select = form.querySelector('select');
        if (select) {
            select.addEventListener('change', async function(event) {
                event.preventDefault();
                // Set the action to select_preset
                const actionInput = form.querySelector('#action-input');
                if (actionInput) {
                    actionInput.value = 'select_preset';
                }
                await submitForm(form, tabName);
            });
        }
        
        // Handle form submission (for Select and Save Preset buttons)
        form.addEventListener('submit', async function(event) {
            event.preventDefault();
            await submitForm(form, tabName);
        });
        
        // Handle all forms in the drum grid (for reverse buttons)
        const drumGrid = document.querySelector('.drum-grid');
        if (drumGrid) {
            drumGrid.addEventListener('submit', async function(event) {
                if (event.target.matches('form')) {
                    event.preventDefault();
                    await submitForm(event.target, tabName);
                }
            });
        }
    } else if (tabName === 'Restore') {
        // Special handling for restore form
        form.addEventListener('submit', async function(event) {
            event.preventDefault();
            await handleRestoreSubmit(form);
        });
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
            // Handle JSON responses for SetManagement
            const contentType = response.headers.get('Content-Type') || '';
            if (tabName === 'SetManagement' && contentType.includes('application/json')) {
                const data = await response.json();
                const container = document.getElementById(tabName);
                const msgDiv = container.querySelector('#result-message');
                if (msgDiv) msgDiv.innerHTML = data.message;
                // Update pad selects
                const padSelect = container.querySelector('select[name="pad_index"]');
                if (padSelect && data.pad_options) {
                    padSelect.innerHTML = data.pad_options;
                    padSelect.selectedIndex = 0;
                }
                const colorSelect = container.querySelector('select[name="pad_color"]');
                if (colorSelect && data.pad_color_options) {
                    colorSelect.innerHTML = data.pad_color_options;
                    colorSelect.selectedIndex = 0;
                }
                // Re-attach handlers
                attachFormHandler(tabName);
                return;
            }
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
                if (typeof initializeTimeStretchModal === 'function') {
                    initializeTimeStretchModal();
                }
            } else if (tabName === 'Restore') {
                initializeRestoreForm();
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
        // New: get slice info from data attributes
        const startPct  = parseFloat(container.dataset.playbackStart)  || 0;
        const lengthPct = parseFloat(container.dataset.playbackLength) || 1;
        const audioPath = container.dataset.audioPath;
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
        
        // Load only the slice of the audio file
        const audioContext = wavesurfer.backend.getAudioContext();
        fetch(audioPath)
          .then(res => res.arrayBuffer())
          .then(data => audioContext.decodeAudioData(data))
          .then(buffer => {
            const duration = buffer.duration;
            const sampleRate = buffer.sampleRate;
            const startSample = Math.floor(startPct * duration * sampleRate);
            const frameCount = Math.floor(lengthPct * duration * sampleRate);
            const slicedBuffer = audioContext.createBuffer(
              buffer.numberOfChannels, frameCount, sampleRate
            );
            for (let ch = 0; ch < buffer.numberOfChannels; ch++) {
              slicedBuffer.copyToChannel(
                buffer.getChannelData(ch).subarray(startSample, startSample + frameCount),
                ch,
                0
              );
            }
            // Load only the slice
            wavesurfer.loadDecodedBuffer(slicedBuffer);
          });
        
        // Handle finish event to reset state
        wavesurfer.on('finish', () => {
            wavesurfer.stop();
        });
        
        // Handle click event
        container.addEventListener('click', function(e) {
            e.stopPropagation();
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
                // --- BEGIN: Detected regions injection ---
                if (window.DETECTED_REGIONS && wavesurfer) {
                    wavesurfer.clearRegions();
                    window.DETECTED_REGIONS.forEach(r => {
                        wavesurfer.addRegion({
                            start: r.start,
                            end: r.end,
                            color: 'rgba(0, 255, 0, 0.2)',
                            drag: false
                        });
                    });
                    delete window.DETECTED_REGIONS;
                    return; // Don't create default contiguous slices
                }
                // --- END: Detected regions injection ---
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
    // Handler for "Slice into even slices" button
    const evenSlicesBtn = document.getElementById('even-slices-btn');
    if (evenSlicesBtn) {
        evenSlicesBtn.addEventListener('click', function() {
            if (!audioReady || !wavesurfer) {
                alert("Audio file must be loaded first.");
                return;
            }
            wavesurfer.stop();
            wavesurfer.clearRegions();
            createContiguousRegions();
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

// --- Detect Transients Button Handler ---
document.addEventListener('DOMContentLoaded', function() {
    const detectBtn = document.getElementById('detect-transients-btn');
    if (detectBtn) {
        detectBtn.addEventListener('click', async function() {
            const fileInput = document.getElementById('file');
            const msg = document.getElementById('transient-detect-message');
            if (!fileInput || !fileInput.files[0]) {
                msg.textContent = "Please select a file first.";
                msg.style.color = "orange";
                return;
            }
            msg.textContent = "Detecting transients...";
            msg.style.color = "#337ab7";
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            try {
                const response = await fetch('/detect-transients', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (data.success && data.regions) {
                    msg.textContent = data.message;
                    msg.style.color = "green";
                    // Update regions on waveform
                    if (typeof wavesurfer !== "undefined" && wavesurfer) {
                        wavesurfer.clearRegions();
                        data.regions.forEach(r => {
                            wavesurfer.addRegion({
                                start: r.start,
                                end: r.end,
                                color: 'rgba(0, 255, 0, 0.2)',
                                drag: false
                            });
                        });
                    }
                } else {
                    msg.textContent = data.message || "No transients detected.";
                    msg.style.color = "orange";
                }
            } catch (err) {
                msg.textContent = "Error detecting transients.";
                msg.style.color = "red";
                console.error(err);
            }
        });
    }
});

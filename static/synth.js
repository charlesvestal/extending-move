document.addEventListener('DOMContentLoaded', function() {
    const presetSelect = document.getElementById('synth-preset-select');
    const polyphonyDisplay = document.getElementById('polyphony-display');

    presetSelect.addEventListener('change', async function() {
        const selectedPath = this.value;
        
        try {
            const response = await fetch(`/preset-data?path=${encodeURIComponent(selectedPath)}`);
            const data = await response.json();
            
            polyphonyDisplay.innerHTML = `
                <p>Polyphony: ${data.polyphony}</p>
            `;
        } catch (error) {
            polyphonyDisplay.innerHTML = `
                <p class="error">Error loading preset data</p>
            `;
            console.error('Error:', error);
        }
    });
});

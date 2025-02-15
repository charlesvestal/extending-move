document.addEventListener('DOMContentLoaded', function() {
    const presetSelect = document.getElementById('preset-select');
    const polyphonyDisplay = document.querySelector('.result-box');

    presetSelect.addEventListener('change', async function() {
        const selectedPath = this.value;
        
        try {
            const response = await fetch(`/preset-data?path=${encodeURIComponent(selectedPath)}`);
            const data = await response.json();
            
            console.log('Received data:', data);  // Debug log
            polyphonyDisplay.innerHTML = `<p>Polyphony: ${data.polyphony}</p>`;
        } catch (error) {
            polyphonyDisplay.innerHTML = `
                <p class="error">Error loading preset data</p>
            `;
            console.error('Error:', error);
        }
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const presetSelect = document.getElementById('preset-select');
    const polyphonyDisplay = document.querySelector('.result-box');
    const toggleButton = document.getElementById('toggle-polyphony');

    async function updatePolyphonyDisplay(data) {
        console.log('Received data:', data);
        polyphonyDisplay.innerHTML = `<p>Polyphony: ${data.polyphony}</p>`;
    }

    presetSelect.addEventListener('change', async function() {
        const selectedPath = this.value;
        
        try {
            const response = await fetch(`/preset-data?path=${encodeURIComponent(selectedPath)}`);
            const data = await response.json();
            
            await updatePolyphonyDisplay(data);
        } catch (error) {
            polyphonyDisplay.innerHTML = `
                <p class="error">Error loading preset data</p>
            `;
            console.error('Error:', error);
        }
    });

    toggleButton.addEventListener('click', async function() {
        const selectedPath = presetSelect.value;
        if (!selectedPath) return;

        try {
            const response = await fetch('/toggle-polyphony', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    path: selectedPath
                })
            });
            const data = await response.json();
            await updatePolyphonyDisplay(data);
        } catch (error) {
            polyphonyDisplay.innerHTML = `
                <p class="error">Error toggling polyphony</p>
            `;
            console.error('Error:', error);
        }
    });
});

/* Shared JavaScript functions */

/**
 * Debounce: returns a debounced version of the provided function.
 * @param {Function} func - The function to debounce.
 * @param {number} wait - The number of milliseconds to delay.
 * @returns {Function} - The debounced function.
 */
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

/**
 * Generates the base preset structure common to both Slice and Chord presets.
 * @param {string} presetName - The name of the preset.
 * @returns {Object} - The base preset JSON object.
 */
function generateBasePreset(presetName) {
  return {
    "$schema": "http://tech.ableton.com/schema/song/1.4.4/devicePreset.json",
    "kind": "instrumentRack",
    "name": presetName,
    "lockId": 1001,
    "lockSeal": -973461132,
    "parameters": {
      "Enabled": true,
      "Macro0": 0.0,
      "Macro1": 0.0,
      "Macro2": 0.0,
      "Macro3": 0.0,
      "Macro4": 0.0,
      "Macro5": 0.0,
      "Macro6": 0.0,
      "Macro7": 0.0
    },
    "chains": [
      {
        "name": "",
        "color": 0,
        "devices": [
          {
            "presetUri": null,
            "kind": "drumRack",
            "name": "",
            "lockId": 1001,
            "lockSeal": 830049224,
            "parameters": {
              "Enabled": true,
              "Macro0": 0.0,
              "Macro1": 0.0,
              "Macro2": 0.0,
              "Macro3": 0.0,
              "Macro4": 0.0,
              "Macro5": 0.0,
              "Macro6": 0.0,
              "Macro7": 0.0
            },
            "chains": [],
            "returnChains": [
              {
                "name": "",
                "color": 0,
                "devices": [
                  {
                    "presetUri": null,
                    "kind": "reverb",
                    "name": "",
                    "parameters": {},
                    "deviceData": {}
                  }
                ],
                "mixer": {
                  "pan": 0.0,
                  "solo-cue": false,
                  "speakerOn": true,
                  "volume": 0.0,
                  "sends": [
                    {
                      "isEnabled": false,
                      "amount": -70.0
                    }
                  ]
                }
              }
            ]
          },
          {
            "presetUri": null,
            "kind": "saturator",
            "name": "Saturator",
            "parameters": {},
            "deviceData": {}
          }
        ],
        "mixer": {
          "pan": 0.0,
          "solo-cue": false,
          "speakerOn": true,
          "volume": 0.0,
          "sends": []
        }
      }
    ]
  };
}

/**
 * Creates a drum cell chain.
 * @param {number} receivingNote - The MIDI note number for the drum cell.
 * @param {string} name - The name of the drum cell.
 * @param {Object} params - Parameters for the drum cell.
 * @param {string|null} sampleUri - The sample URI to use (or null).
 * @returns {Object} - A drum cell chain object.
 */
function createDrumCellChain(receivingNote, name, params, sampleUri) {
  return {
    "name": name,
    "color": 0,
    "devices": [
      {
        "presetUri": null,
        "kind": "drumCell",
        "name": name,
        "parameters": params,
        "deviceData": {
          "sampleUri": sampleUri || null
        }
      }
    ],
    "mixer": {
      "pan": 0.0,
      "solo-cue": false,
      "speakerOn": true,
      "volume": 0.0,
      "sends": [
        {
          "isEnabled": true,
          "amount": -70.0
        }
      ]
    },
    "drumZoneSettings": {
      "receivingNote": receivingNote,
      "sendingNote": 60,
      "chokeGroup": 1
    }
  };
}
;(function(root, factory) {
  if (typeof define === 'function' && define.amd) {
    define(['pixi.js', 'teoria', 'musical-scale-colors'], factory);
  } else if (typeof exports === 'object') {
    module.exports = factory(require('pixi.js'), require('teoria'), require('musical-scale-colors'));
  } else {
    root.pixiPianoRoll = factory(root.PIXI, root.teoria, root.musicalScaleColors);
  }
}(this, function(pixi, teoria, musicalScaleColors) {
'use strict';

var _slicedToArray = (function () { function sliceIterator(arr, i) { var _arr = []; var _n = true; var _d = false; var _e = undefined; try { for (var _i = arr[Symbol.iterator](), _s; !(_n = (_s = _i.next()).done); _n = true) { _arr.push(_s.value); if (i && _arr.length === i) break; } } catch (err) { _d = true; _e = err; } finally { try { if (!_n && _i["return"]) _i["return"](); } finally { if (_d) throw _e; } } return _arr; } return function (arr, i) { if (Array.isArray(arr)) { return arr; } else if (Symbol.iterator in Object(arr)) { return sliceIterator(arr, i); } else { throw new TypeError("Invalid attempt to destructure non-iterable instance"); } }; })();

/**
 * JavaScript 2D WebGL / Canvas animated piano roll
 * @module pixiPianoRoll
 * @author Matthew Hasbach
 * @copyright Matthew Hasbach 2015
 * @license MIT
 */

/**
 * Playback position expressed in bars:quarters:sixteenths format (e.g. `"1:2:0"`)
 * @typedef {string} transportTime
 * @global
 */

/**
 * Musical note expressed in [Scientific notation]{@link https://en.wikipedia.org/wiki/Scientific_pitch_notation}, [Helmholtz notation]{@link https://en.wikipedia.org/wiki/Helmholtz_pitch_notation}, [piano key number]{@link https://en.wikipedia.org/wiki/Piano_key_frequencies}, [audio frequency]{@link https://en.wikipedia.org/wiki/Audio_frequency} (the closest note will be used), or [MIDI]{@link https://en.wikipedia.org/wiki/MIDI} note number
 * @typedef {string|number} note
 * @global
 */

/**
 * Note duration expressed as a number (e.g. `1` for a whole note) or string (e.g. `"4n"` for a quarter note)
 * @typedef {string|number} noteDuration
 * @global
 */

/**
 * See the typedefs for [transportTime]{@link transportTime}, [note]{@link note}, and [noteDuration]{@link noteDuration}
 * @typedef {Array.<Array<transportTime, note, noteDuration>>} noteData
 * @global
 */

/**
 * Instantiate a pixiPianoRoll
 * @alias module:pixiPianoRoll
 * @param {Object} opt - Options object
 * @param {number} [opt.width=900] - Width of the piano roll
 * @param {number} [opt.height=400] - Height of the piano roll
 * @param {number} [opt.pianoKeyWidth=125] - Width of the piano keys
 * @param {number|Object<number>} [opt.noteColor=musicalScaleColors.dDJameson] - Hexadecimal color of every note or object that has pitch class (chroma) property names and hexadecimal color values. See [musical-scale-colors]{@link https://github.com/mjhasbach/musical-scale-colors} for palettes (including the default).
 * @param {number} [opt.noteColor=0x333333] - Hexadecimal color of the grid lines
 * @param {number} [opt.noteColor=0] - Hexadecimal color of the background
 * @param {number} [opt.bpm=140] - Beats per minute
 * @param {boolean} [opt.activateKeys=true] - If true, the color of the piano keys will change to the color of the notes that intersect them
 * @param {boolean} [opt.antialias=true] - Whether or not the renderer will use antialiasing
 * @param {number} [opt.zoom=4] - Amount of visible measures
 * @param {number} [opt.resolution=1] - Amount of vertical grid lines per measure
 * @param {transportTime} [opt.time=0:0:0] - The [transportTime]{@link transportTime} at which playback will begin
 * @param {string} [opt.renderer=WebGLRenderer] - Determines the renderer type. Must be `"WebGLRenderer"` or `"CanvasRenderer"`.
 * @param {string} [opt.noteFormat=String] - The format of the [notes]{@link note} in `opt.noteData`. `"String"` for scientific or Helmholtz notation, `"Key"` for piano key numbers, `"Frequency"` for audio frequencies, or `"MIDI"` for MIDI note numbers.
 * @param {noteData} [opt.noteData=[]] - Note data
 * @returns {pianoRollAPI}
 * @example
var pianoRoll = pixiPianoRoll({
    width: 900,
    height: 400,
    noteColor: 0xdb000f,
    gridLineColor: 0x333333,
    backgroundColor: 0x1a0002,
    bpm: 140,
    antialias: true,
    zoom: 4,
    resolution: 2,
    time: '0:0:0',
    renderer: 'WebGLRenderer',
    noteFormat: 'String',
    noteData: [
        ['0:0:0', 'C4', '2n'],
        ['0:0:0', 'D4', '2n'],
        ['0:0:0', 'E4', '2n'],
        ['0:2:0', 'B4', '4n'],
        ['0:3:0', 'A#4', '4n']
    ]
});

document.getElementsByTagName('body')[0].appendChild(pianoRoll.view);

pianoRoll.playback.play();
 */
function pixiPianoRoll(opt) {
    var colors = {
        black: 0,
        white: 0xFFFFFF
    };

    opt = Object.assign({
        width: 900,
        height: 400,
        pianoKeyWidth: 125,
        noteColor: musicalScaleColors.dDJameson,
        gridLineColor: 0x333333,
        backgroundColor: colors.black,
        bpm: 140,
        activateKeys: true,
        antialias: true,
        zoom: 4,
        resolution: 1,
        time: '0:0:0',
        renderer: 'WebGLRenderer',
        noteFormat: 'String',
        noteData: []
    }, opt);

    var keys = undefined,
        lastTime = undefined,
        beatsPerMs = undefined,
        pxMovementPerMs = undefined,
        noteContainer = undefined,
        noteRange = undefined,
        noteRangeDiff = undefined,
        noteHeight = undefined,
        innerNoteHeight = undefined,
        pianoContainer = undefined,
        barWidth = undefined,
        beatWidth = undefined,
        sixteenthWidth = undefined,
        gridLineWidth = undefined,
        halfGridLineWidth = undefined,
        gridLineSpacing = undefined,
        activeKeys = undefined,
        playing = false,
        stage = new pixi.Container(),
        rollContainer = new pixi.Container(),
        gridlineContainers = {
        main: new pixi.Container()
    },
        renderer = new pixi[opt.renderer](opt.width, opt.height, {
        antialias: opt.antialias,
        autoResize: true
    });

    function getTeoriaNote(note) {
        var noteObj = teoria.note['from' + opt.noteFormat](note);

        return opt.noteFormat === 'Frequency' ? noteObj.note : noteObj;
    }

    function getNoteRange() {
        var min = undefined,
            max = undefined;

        var _iteratorNormalCompletion = true;
        var _didIteratorError = false;
        var _iteratorError = undefined;

        try {
            for (var _iterator = opt.noteData[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = true) {
                var _step$value = _slicedToArray(_step.value, 2);

                var note = _step$value[1];

                var keyNumber = getTeoriaNote(note).key();

                if (keyNumber < min || typeof min !== 'number') {
                    min = keyNumber;
                }
                if (keyNumber > max || typeof max !== 'number') {
                    max = keyNumber;
                }
            }
        } catch (err) {
            _didIteratorError = true;
            _iteratorError = err;
        } finally {
            try {
                if (!_iteratorNormalCompletion && _iterator.return) {
                    _iterator.return();
                }
            } finally {
                if (_didIteratorError) {
                    throw _iteratorError;
                }
            }
        }

        return { min: min - 1, max: max };
    }

    function drawPianoKey(key, active) {
        return (key.graphic || new pixi.Graphics()).clear().beginFill(active ? key.activeColor : key.color).lineStyle(key.color === colors.white ? noteHeight / 10 : 0, colors.black).drawRect(0, key.y, key.width, key.height).endFill();
    }

    function drawPianoKeys() {
        var whiteKeys = [],
            blackKeys = [],
            blackKeyWidth = opt.pianoKeyWidth / 1.575;

        keys = {};
        activeKeys = new Set();
        stage.removeChild(pianoContainer);
        pianoContainer = new pixi.Container();

        for (var i = noteRange.min; i < noteRange.max + 2; i++) {
            var y = opt.height + (noteRange.min - i) * noteHeight,
                note = teoria.note.fromKey(i),
                chroma = note.chroma(),
                key = {
                keyNumber: note.key(),
                activeColor: typeof opt.noteColor === 'number' ? opt.noteColor : opt.noteColor[chroma]
            };

            if (new Set([0, 2, 4, 5, 7, 9, 11]).has(chroma)) {
                whiteKeys.push(Object.assign(key, {
                    y: y + (new Set([4, 11]).has(chroma) ? 0 : -noteHeight / 2),
                    width: opt.pianoKeyWidth,
                    height: new Set([2, 7, 9]).has(chroma) ? noteHeight * 2 : noteHeight * 1.5,
                    color: colors.white
                }));
            } else {
                blackKeys.push(Object.assign(key, {
                    y: y,
                    width: blackKeyWidth,
                    height: noteHeight,
                    color: colors.black
                }));
            }
        }

        whiteKeys.concat(blackKeys).forEach(function (key) {
            var pixiKey = drawPianoKey(key);

            keys[key.keyNumber] = Object.assign(key, { graphic: pixiKey });
            pianoContainer.addChild(pixiKey);
        });

        stage.addChild(pianoContainer);
    }

    function transportTimeToX(transportTime, isNote) {
        if (!transportTime) {
            return 0;
        }

        var _transportTime$split = transportTime.split(':');

        var _transportTime$split2 = _slicedToArray(_transportTime$split, 3);

        var bar = _transportTime$split2[0];
        var _transportTime$split3 = _transportTime$split2[1];
        var quarter = _transportTime$split3 === undefined ? 0 : _transportTime$split3;
        var _transportTime$split4 = _transportTime$split2[2];
        var sixteenth = _transportTime$split4 === undefined ? 0 : _transportTime$split4;
        var x = barWidth * bar + beatWidth * quarter + sixteenthWidth * sixteenth;

        return isNote ? x : opt.pianoKeyWidth - x;
    }

    function drawNotes() {
        var oldContainer = rollContainer.removeChild(noteContainer);

        noteContainer = new pixi.Container();

        var _iteratorNormalCompletion2 = true;
        var _didIteratorError2 = false;
        var _iteratorError2 = undefined;

        try {
            for (var _iterator2 = opt.noteData[Symbol.iterator](), _step2; !(_iteratorNormalCompletion2 = (_step2 = _iterator2.next()).done); _iteratorNormalCompletion2 = true) {
                var _step2$value = _slicedToArray(_step2.value, 3);

                var transportTime = _step2$value[0];
                var note = _step2$value[1];
                var duration = _step2$value[2];

                var pixiNote = new pixi.Graphics(),
                    teoriaNote = getTeoriaNote(note),
                    keyNumber = teoriaNote.key(),
                    color = typeof opt.noteColor === 'number' ? opt.noteColor : opt.noteColor[teoriaNote.chroma()];

                pixiNote.beginFill(color).drawRect(0, 0, barWidth / parseInt(duration), innerNoteHeight).endFill();

                pixiNote.x = transportTimeToX(transportTime, true) + halfGridLineWidth;
                pixiNote.y = opt.height - (keyNumber - noteRange.min) * noteHeight + halfGridLineWidth;
                pixiNote.keyNumber = keyNumber;

                noteContainer.addChild(pixiNote);
            }
        } catch (err) {
            _didIteratorError2 = true;
            _iteratorError2 = err;
        } finally {
            try {
                if (!_iteratorNormalCompletion2 && _iterator2.return) {
                    _iterator2.return();
                }
            } finally {
                if (_didIteratorError2) {
                    throw _iteratorError2;
                }
            }
        }

        noteContainer.x = oldContainer ? oldContainer.x : transportTimeToX(opt.time);
        rollContainer.addChild(noteContainer);
    }

    function moveVerticalGridLines(horizontalMovement) {
        var verticalGridlines = gridlineContainers.vertical.children;

        var _iteratorNormalCompletion3 = true;
        var _didIteratorError3 = false;
        var _iteratorError3 = undefined;

        try {
            for (var _iterator3 = verticalGridlines[Symbol.iterator](), _step3; !(_iteratorNormalCompletion3 = (_step3 = _iterator3.next()).done); _iteratorNormalCompletion3 = true) {
                var line = _step3.value;

                line.x -= horizontalMovement;
            }
        } catch (err) {
            _didIteratorError3 = true;
            _iteratorError3 = err;
        } finally {
            try {
                if (!_iteratorNormalCompletion3 && _iterator3.return) {
                    _iterator3.return();
                }
            } finally {
                if (_didIteratorError3) {
                    throw _iteratorError3;
                }
            }
        }

        if (verticalGridlines[0].x + gridLineWidth < opt.pianoKeyWidth) {
            var line = gridlineContainers.vertical.removeChildAt(0);

            line.x = verticalGridlines[verticalGridlines.length - 1].x + gridLineSpacing;

            gridlineContainers.vertical.addChild(line);
        }
    }

    function getFirstVerticalGridLineX(transportX) {
        var x = transportX;

        while (x + gridLineSpacing < opt.pianoKeyWidth) {
            x += gridLineSpacing;
        }

        return x;
    }

    function drawGridlines(type) {
        var i = undefined;

        if (!type || type === 'horizontal') {
            gridlineContainers.main.removeChild(gridlineContainers.horizontal);
            gridlineContainers.horizontal = new pixi.Container();

            for (i = 0; i < noteRangeDiff + 1; i++) {
                gridlineContainers.horizontal.addChild(new pixi.Graphics().beginFill(opt.gridLineColor).drawRect(0, i * noteHeight - halfGridLineWidth, opt.width, gridLineWidth).endFill());
            }

            gridlineContainers.main.addChild(gridlineContainers.horizontal);
        }

        if (!type || type === 'vertical') {
            var offset = getFirstVerticalGridLineX(noteContainer ? noteContainer.x : transportTimeToX(opt.time));

            gridlineContainers.main.removeChild(gridlineContainers.vertical);
            gridlineContainers.vertical = new pixi.Container();

            for (i = 0; i < opt.zoom * opt.resolution + 1; i++) {
                var line = new pixi.Graphics().beginFill(opt.gridLineColor).drawRect(0, 0, gridLineWidth, opt.height).endFill();

                line.x = offset + i * gridLineSpacing - halfGridLineWidth;

                gridlineContainers.vertical.addChild(line);
            }

            gridlineContainers.main.addChild(gridlineContainers.vertical);
        }

        rollContainer.addChild(gridlineContainers.main);
    }

    function activateKeys() {
        if (!opt.activateKeys) {
            return;
        }

        var intersectedKeys = new Set();

        var _iteratorNormalCompletion4 = true;
        var _didIteratorError4 = false;
        var _iteratorError4 = undefined;

        try {
            for (var _iterator4 = noteContainer.children[Symbol.iterator](), _step4; !(_iteratorNormalCompletion4 = (_step4 = _iterator4.next()).done); _iteratorNormalCompletion4 = true) {
                var note = _step4.value;

                if (note.containsPoint(new pixi.Point(opt.pianoKeyWidth, note.y))) {
                    intersectedKeys.add(note.keyNumber);
                }
            }
        } catch (err) {
            _didIteratorError4 = true;
            _iteratorError4 = err;
        } finally {
            try {
                if (!_iteratorNormalCompletion4 && _iterator4.return) {
                    _iterator4.return();
                }
            } finally {
                if (_didIteratorError4) {
                    throw _iteratorError4;
                }
            }
        }

        var _iteratorNormalCompletion5 = true;
        var _didIteratorError5 = false;
        var _iteratorError5 = undefined;

        try {
            for (var _iterator5 = intersectedKeys[Symbol.iterator](), _step5; !(_iteratorNormalCompletion5 = (_step5 = _iterator5.next()).done); _iteratorNormalCompletion5 = true) {
                var intersectedKey = _step5.value;

                if (!activeKeys.has(intersectedKey)) {
                    var key = keys[intersectedKey];

                    drawPianoKey(key, true);
                    activeKeys.add(intersectedKey);
                }
            }
        } catch (err) {
            _didIteratorError5 = true;
            _iteratorError5 = err;
        } finally {
            try {
                if (!_iteratorNormalCompletion5 && _iterator5.return) {
                    _iterator5.return();
                }
            } finally {
                if (_didIteratorError5) {
                    throw _iteratorError5;
                }
            }
        }

        var _iteratorNormalCompletion6 = true;
        var _didIteratorError6 = false;
        var _iteratorError6 = undefined;

        try {
            for (var _iterator6 = activeKeys[Symbol.iterator](), _step6; !(_iteratorNormalCompletion6 = (_step6 = _iterator6.next()).done); _iteratorNormalCompletion6 = true) {
                var activeKey = _step6.value;

                if (!intersectedKeys.has(activeKey)) {
                    var key = keys[activeKey];

                    drawPianoKey(key);
                    activeKeys.delete(activeKey);
                }
            }
        } catch (err) {
            _didIteratorError6 = true;
            _iteratorError6 = err;
        } finally {
            try {
                if (!_iteratorNormalCompletion6 && _iterator6.return) {
                    _iterator6.return();
                }
            } finally {
                if (_didIteratorError6) {
                    throw _iteratorError6;
                }
            }
        }
    }

    function animate(frameTime) {
        if (!lastTime) {
            lastTime = frameTime;
        }

        var timeDiff = frameTime - lastTime,
            horizontalMovement = timeDiff * pxMovementPerMs;

        noteContainer.x = noteContainer.x - horizontalMovement;
        moveVerticalGridLines(horizontalMovement);
        activateKeys();
        lastTime = frameTime;
        renderer.render(stage);
        playing ? requestAnimationFrame(animate) : lastTime = null;
    }

    function calculate() {
        noteRange = getNoteRange(opt.noteData);
        noteRangeDiff = noteRange.max - noteRange.min;
        barWidth = (opt.width - opt.pianoKeyWidth) / opt.zoom;
        beatWidth = (opt.width - opt.pianoKeyWidth) / (opt.zoom * 4);
        sixteenthWidth = beatWidth / 4;
        gridLineWidth = barWidth / 100;
        halfGridLineWidth = gridLineWidth / 2;
        gridLineSpacing = barWidth / opt.resolution;
        beatsPerMs = opt.bpm / 60 / 1000;
        pxMovementPerMs = beatWidth * beatsPerMs;
        noteHeight = opt.height / noteRangeDiff;
        innerNoteHeight = noteHeight - gridLineWidth;
    }

    (function init() {
        stage.addChild(rollContainer);
        calculate();
        drawGridlines();
        drawNotes();
        drawPianoKeys();
        renderer.backgroundColor = opt.backgroundColor;
        renderer.render(stage);
    })();

    /**
     * The piano roll API
     * @typedef pianoRollAPI
     * @type {Object}
     * @global
     */
    var pianoRollAPI = {
        /**
         * Contains methods that control playback
         * @memberof pianoRollAPI
         * @type {Object}
         */
        playback: {
            /**
             * Pause if playing or play if paused
             * @param {transportTime} [time] - If paused, the position to begin playing. If omitted, playback will begin at the current position.
             */

            toggle: function toggle(time) {
                playing ? pianoRollAPI.playback.pause() : pianoRollAPI.playback.play(time);
            },

            /**
             * Begin playback
             * @param {transportTime} [time] - The position to begin playing. If omitted, playback will begin at the current position.
             */
            play: function play(time) {
                if (!playing) {
                    if (time) {
                        pianoRollAPI.playback.seek(time);
                    }

                    playing = true;
                    requestAnimationFrame(animate);
                }
            },

            /**
             * Pause playback
             */
            pause: function pause() {
                playing = false;
            },

            /**
             * Change the playback position
             * @param {transportTime} time - The new playback position
             */
            seek: function seek(time) {
                opt.time = time;

                noteContainer.x = transportTimeToX(time);
                drawGridlines('vertical');
                rollContainer.addChild(rollContainer.removeChild(noteContainer));
                renderer.render(stage);
            }
        },
        /**
         * Change the bpm by changing this property
         * @memberof pianoRollAPI
         * @type {number}
         */
        set bpm(bpm) {
            opt.bpm = bpm;
            calculate();
        },
        /**
         * Change the zoom by changing this property
         * @memberof pianoRollAPI
         * @type {number}
         */
        set zoom(zoom) {
            opt.zoom = zoom;
            calculate();
            drawGridlines();
            drawNotes();
            renderer.render(stage);
        },
        /**
         * Change the resolution by changing this property
         * @memberof pianoRollAPI
         * @type {number}
         */
        set resolution(resolution) {
            opt.resolution = resolution;
            calculate();
            drawGridlines('vertical');
            rollContainer.addChild(rollContainer.removeChild(noteContainer));
            renderer.render(stage);
        },
        /**
         * Change the note data by changing this property
         * @memberof pianoRollAPI
         * @type {noteData}
         */
        set noteData(noteData) {
            opt.noteData = noteData;
            calculate();
            drawGridlines('horizontal');
            drawNotes();
            drawPianoKeys();
            renderer.render(stage);
        },
        /**
         * Whether or not playback is ongoing
         * @memberof pianoRollAPI
         * @type {boolean}
         * @readonly
         */
        get playing() {
            return playing;
        },
        /**
         * The piano roll canvas element
         * @memberof pianoRollAPI
         * @type {HTMLElement}
         * @readonly
         */
        get view() {
            return renderer.view;
        }
    };

    return pianoRollAPI;
}
return pixiPianoRoll;
}));

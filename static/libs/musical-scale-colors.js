;
(function(root, factory) {
    if (typeof define === 'function' && define.amd) {
        define([], factory);
    } else if (typeof exports === 'object') {
        module.exports = factory();
    } else {
        root.musicalScaleColors = factory();
    }
}(this, function() {
    // http://rhythmiclight.com/archives/ideas/colorscales.html
    return {
        louisBertrandCastel: {
            0: 0x1C0D82,  // blue
            1: 0x1B9081,  // blue-green
            2: 0x149033,  // green
            3: 0x709226,  // olive green
            4: 0xF5F43C,  // yellow
            5: 0xF5D23B,  // yellow-orange
            6: 0xF88010,  // orange
            7: 0xFA0B0C,  // red
            8: 0xA00C09,  // crimson
            9: 0xD71386,  // violet
            10: 0x4B0E7D, // agate
            11: 0x7F087C  // indigo
        },
        dDJameson: {
            0: 0xFA0B0C,  // red
            1: 0xF44712,  // red-orange
            2: 0xF88010,  // orange
            3: 0xF5D23B,  // orange-yellow
            4: 0xF5F43C,  // yellow
            5: 0x149033,  // green
            6: 0x1B9081,  // green-blue
            7: 0x1C0D82,  // blue
            8: 0x4B0E7D,  // blue-purple
            9: 0x7F087C,  // purple
            10: 0xA61586, // purple-violet
            11: 0xD71285  // violet
        },
        theodorSeemann: {
            0: 0x6A1C1C,  // carmine
            1: 0xFA0B0C,  // scarlet
            2: 0xFF7D05,  // orange
            3: 0xFCD533,  // yellow-orange
            4: 0xF5F43C,  // yellow
            5: 0x169034,  // green
            6: 0x1B9081,  // green blue
            7: 0x1C0D82,  // blue
            8: 0x7F087C,  // indigo
            9: 0xD71386,  // violet
            10: 0x6A1C1C, // brown
            11: 0x070707  // black
        },
        aWallaceRimington: {
            0: 0xFA0B0C,  // deep red
            1: 0xA00C09,  // crimson
            2: 0xF44712,  // orange-crimson
            3: 0xF88010,  // orange
            4: 0xF5F43C,  // yellow
            5: 0x709226,  // yellow-green
            6: 0x149033,  // green
            7: 0x26A680,  // blueish green
            8: 0x1B9081,  // blue-green
            9: 0x7F087C,  // indigo
            10: 0x1C0D82, // deep blue
            11: 0xD71386  // violet
        },
        hHelmholtz: {
            0: 0xF5F43C,  // yellow
            1: 0x149033,  // green
            2: 0x1B9081,  // greenish blue
            3: 0x1C5BA0,  // cayan-blue
            4: 0x7F087C,  // indigo blue
            5: 0xD71386,  // violet
            6: 0x9D0E55,  // end of red
            7: 0xFA0B0C,  // red
            8: 0xD32C0A,  // red
            9: 0xD32C0A,  // red
            10: 0xD91951, // red orange
            11: 0xF17A0F  // orange
        },
        aScriabin: {
            0: 0xFA0B0C,  // red
            1: 0xD71386,  // violet
            2: 0xF5F43C,  // yellow
            3: 0x5A5685,  // steely with the glint of metal
            4: 0x1C5BA0,  // pearly blue the shimmer of moonshine
            5: 0xA00C09,  // dark red
            6: 0x1C0D82,  // bright blue
            7: 0xF88010,  // rosy orange
            8: 0x7F0A7C,  // purple
            9: 0x149033,  // green
            10: 0x5A5685, // steely with a glint of metal
            11: 0x1C5BA0  // pearly blue the shimmer of moonshine
        },
        aBernardKlein: {
            0: 0xC40A09,  // dark red
            1: 0xFA0B0C,  // red
            2: 0xF44712,  // red orange
            3: 0xF88010,  // orange
            4: 0xF5F43C,  // yellow
            5: 0xBCE039,  // yellow green
            6: 0x149033,  // green
            7: 0x1B9081,  // blue-green
            8: 0x1C0D82,  // blue
            9: 0x781887,  // blue violet
            10: 0xD71386, // violet
            11: 0x9D0E55  // dark violet
        },
        iJBelmont: {
            0: 0xFA0B0C,  // red
            1: 0xF44712,  // red-orange
            2: 0xF88010,  // orange
            3: 0xF6D111,  // yellow-orange
            4: 0xF5F43C,  // yellow
            5: 0xBCE039,  // yellow-green
            6: 0x138F32,  // green
            7: 0x1B9081,  // blue-green
            8: 0x1C0D82,  // blue
            9: 0xA51585,  // blue-violet
            10: 0xD71386, // violet
            11: 0xAD0E48  // red-violet
        },
        sZieverink: {
            0: 0xBCE039,  // yellow/green
            1: 0x149033,  // green
            2: 0x1B9081,  // blue/green
            3: 0x1C0D82,  // blue
            4: 0x7F087C,  // indigo
            5: 0xD71386,  // violet
            6: 0x6F0D45,  // ultra violet
            7: 0xA00C09,  // infra red
            8: 0xFA0B0C,  // red
            9: 0xF88010,  // orange
            10: 0xEDF087, // yellow/white
            11: 0xF5F43C  // yellow
        }
    };
}));

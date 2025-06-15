# extending-move

Tools for extending the Ableton Move. This project provides a companion webserver that runs alongside the official Move server, accessible at ``move.local:909``!

![CleanShot 2025-06-11 at 14 22 41](https://github.com/user-attachments/assets/e3ef7449-67e8-4b5e-958f-2c628a90b64d)


[Demo on YouTube](https://www.youtube.com/watch?v=MCmaCifzgbg)

## Installation instructions

[Quick installation video](https://youtu.be/gPiR7Zyu3lc)
- Clone or download the repository.
- Run utility-scripts/setup-ssh-and-install-on-move.command
- Follow the instructions!
  
## Features

Here’s what you can do with Extending Move:

- **Set Restoration**
  - Upload and restore Move Sets (.ablbundle or .abl)
  - Choose target pad and color

- **Drift, Wavetable and melodicSampler Preset Editor**
  - Modify any preset parameter value or create a preset from scratch
  - Manage macro knob assignments and preview their effect on mapped parameters in real time
  - Preview samples and see region and envelopes on melodicSampler presets

- **Chord Kit Generation**
  - Create chord variations from any WAV file
  - Choose from various chords, voicing and transpositions

- **Sliced Kit Creation**
  - Use a visual slicer to create drum kits from WAV files with up to 16 slices
  - Auto-slice to even slices or transients
  - Create choke group configurations or use Gate and Drum kit style presets

- **Drum Rack Inspector**
  - View and download samples in a drum rack preset
  - Reverse or time stretch samples to a target BPM and length with different algorithms for melodic or rhythmic content

- **Set Inspector**
  - View notes and envelopes for sets and clips
  - Edit envelopes and draw your own curves
- **Clip Editor**
  - Modify clip notes and envelopes in a piano roll
  - Adjust region length and loop points

- **Sample Reversal**
  - Create reversed versions of any WAV file
  - Use reversed file in drum kit or sample presets    
 
- **MIDI Import**
  - Upload MIDI files to create new Melodic or Drum Sets
  - New Sets created with either a default Drift or 808 kit for customization


## Contributors

Many thanks to the contributors who have helped discover and document Move's capabilities:
bobbyd, void, deets, djhardrich, fedpep, manuz, poga, void, and many more.

Interested in chatting about more Move hacking? Come talk to us on [Discord](https://discord.gg/yP7SjqDrZG).

## Documentation

Check the [Wiki](https://github.com/charlesvestal/extending-move/wiki) for:
- Detailed Move documentation
- Hardware insights
- Development tips
- Troubleshooting guides

## Disclaimer

This project is not affiliated with, authorized by, or endorsed by Ableton. Use at your own risk. The authors cannot be held responsible for any damage or issues that may occur. Always refer to official documentation when modifying hardware.

This project includes a statically linked binary of Rubber Band. The source code for Rubber Band is available under GPLv2 at [https://breakfastquay.com/rubberband/](https://breakfastquay.com/rubberband/).

> These tools are third-party and require SSH access. That means:
> * There’s a real risk (though unlikely) of breaking things. You are accessing the Move in ways it was not designed to do.
> * Ableton can’t offer individual support if something goes wrong.
> * If issues do arise, the documented restore procedure is the fallback – you use this at your own risk. Information on this procedure can be found in Center Code under [Documentation](https://ableton.centercode.com/project/article/item.html?cap=ecd3942a1fe3405eb27a806608401a0b&arttypeid={e70be312-f44a-418b-bb74-ed1030e3a49a}&artid={C0A2D9E2-D52F-4DEB-8BEE-356B65C8942E}).

## License

This project is licensed under the [MIT License](LICENSE).

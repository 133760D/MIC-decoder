# MIC Decoder
## About This Project
This project is a fun initiative. Using native Python libraries, this script can decode simple Machine Identification Code (MIC) patterns from various printers.

## Features
- Decodes MIC patterns from different printers
- Graphical interface (keyboard accessible)

### Supported printers:
*Currently, the project only cover one pattern which is the publicly identified 15x8 grid pattern from Xerox. This pattern is however used across many brands with slight modifications.*
- Xerox
    - DocuColor
    - Phaser
- Dell
    - ColorLaser
- Epson
    - Aculaser C4000
    - Aculaser C3000

more printers might be using the same pattern.

### Todo:
- add the partially decoded quaternary pattern, universal to many printers
- script to make dots easily visible from a paper scan (image and pdf); should be easy to implement with openCV
- Machine Learning to automatically fill in the dots and detect pattern. (Maybe use a two-stage model? First detect pattern then detect the dots.)
- decode more patterns, add more printers (see the datamining [readme](datamining/README.md))

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.



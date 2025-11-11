# Panel QC - Electric Panel Buzzing Detection

## Overview

Panel QC is a Python-based audio monitoring tool designed to detect and analyze buzzing sounds in electrical panels. The application uses real-time audio capture and signal processing techniques to identify potential electrical issues by monitoring for characteristic buzzing frequencies that may indicate problems such as loose connections, failing breakers, or other electrical anomalies.

## Features

- **Real-time Audio Monitoring**: Continuously captures audio input from microphones or other audio devices
- **Buzzing Detection**: Identifies characteristic buzzing patterns associated with electrical panel issues
- **Automated Analysis**: Processes audio streams to detect anomalous sounds that may indicate electrical problems
- **Quality Control**: Provides quality control metrics for electrical panel maintenance and monitoring

## Use Cases

This tool is particularly useful for:

- **Preventive Maintenance**: Early detection of electrical panel issues before they become critical
- **Quality Assurance**: Monitoring electrical installations in residential, commercial, or industrial settings
- **Safety Inspections**: Identifying potential electrical hazards through audio signatures
- **Remote Monitoring**: Continuous surveillance of electrical systems in unmanned facilities

## Prerequisites

Before installing Panel QC, ensure you have the following:

- **Python 3.7+**: The application requires Python 3.7 or higher
- **Audio Hardware**: A microphone or audio input device capable of capturing sounds in the 50-120 Hz range (typical electrical buzzing frequencies)
- **Operating System**: Compatible with Linux, macOS, and Windows

### System Dependencies

Depending on your operating system, you may need to install additional audio libraries:

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get update
sudo apt-get install libasound2-dev portaudio19-dev
sudo apt-get install libatlas-base-dev  # Required for numpy
```

**macOS:**
```bash
brew install portaudio
```

**Windows:**
Most dependencies are included with Python packages. Ensure you have Microsoft Visual C++ Build Tools installed for compiling certain libraries.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/ddicostanzo/panel_qc.git
cd panel_qc
```

### 2. Create a Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/macOS
# or
venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Setup Script (Linux/macOS)

If a setup script is provided, execute it to configure the environment:

```bash
chmod +x setup.sh
./setup.sh
```

## Usage

### Basic Operation

To start monitoring for buzzing sounds:

```bash
python audio_capture.py
```

### Command-Line Options

The application may support various command-line arguments (adjust based on actual implementation):

```bash
python audio_capture.py --device <device_id>  # Specify audio input device
python audio_capture.py --threshold <value>   # Set detection threshold
python audio_capture.py --duration <seconds>  # Set monitoring duration
python audio_capture.py --output <filename>   # Save results to file
```

### Listing Available Audio Devices

To see all available audio input devices on your system:

```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

### Configuration

Configuration parameters can typically be adjusted in a settings file or through command-line arguments:

- **Sample Rate**: Recommended 44100 Hz or 48000 Hz
- **Chunk Size**: Buffer size for audio processing (typically 1024-2048 samples)
- **Detection Threshold**: Sensitivity level for buzzing detection
- **Frequency Range**: Target frequency bands for electrical buzzing (typically 50-120 Hz and harmonics)

## How It Works

Panel QC employs several signal processing techniques to detect electrical panel buzzing:

1. **Audio Capture**: Uses PyAudio or sounddevice library to capture real-time audio from the specified input device

2. **Signal Processing**:
   - Fast Fourier Transform (FFT) to analyze frequency components
   - Bandpass filtering to isolate frequencies associated with electrical buzzing (50/60 Hz and harmonics)
   - Peak detection to identify characteristic buzzing patterns

3. **Pattern Recognition**:
   - Compares detected frequencies against known electrical buzzing signatures
   - Identifies sustained tones that indicate potential electrical issues
   - Filters out ambient noise and transient sounds

4. **Alert Generation**: Triggers notifications when buzzing patterns exceed configured thresholds

## Technical Details

### Typical Dependencies

- **numpy**: Numerical computing and array operations
- **scipy**: Scientific computing and signal processing algorithms
- **sounddevice** or **pyaudio**: Audio I/O and device interfacing
- **matplotlib** (optional): Visualization of frequency spectra

### Audio Processing Pipeline

```
Microphone → Audio Capture → Pre-processing → FFT Analysis → 
Peak Detection → Pattern Matching → Alert/Logging
```

### Key Frequency Bands

Electrical buzzing typically manifests at:
- **50 Hz** (Europe, Asia, Africa, Australia - AC mains frequency)
- **60 Hz** (North America, parts of South America - AC mains frequency)
- **Harmonics**: 100/120 Hz, 150/180 Hz, 200/240 Hz, etc.

## Output

The application may provide output in various formats:

- **Console Output**: Real-time status and detection alerts
- **Log Files**: Timestamped records of detected events
- **Audio Recordings**: Saved snippets of detected buzzing sounds
- **Visualization**: Spectrograms or frequency plots (if enabled)

## Troubleshooting

### No Audio Device Found
- Verify your microphone is properly connected
- Check system audio settings
- List available devices using the command provided in the Usage section
- Ensure proper permissions for audio device access

### High False Positive Rate
- Adjust detection threshold
- Ensure microphone is positioned close to the electrical panel
- Minimize background noise in the monitoring environment
- Consider using a directional microphone

### Buffer Underrun/Overrun Errors
- Increase buffer size (CHUNK parameter)
- Reduce sample rate if system resources are limited
- Close other audio applications

### Installation Issues
- Ensure all system dependencies are installed
- Update pip: `pip install --upgrade pip`
- If compilation fails, try installing pre-built wheels

## Safety Considerations

**WARNING**: This tool is designed for non-invasive audio monitoring only. 

- **Never open electrical panels** unless you are a qualified electrician
- **Maintain safe distances** from electrical equipment
- Use this tool as a **diagnostic aid only**, not a replacement for professional inspection
- If buzzing is detected, **contact a licensed electrician** for proper investigation and repair

## Contributing

Contributions to Panel QC are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

Please ensure your code follows Python best practices and includes appropriate documentation.

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0). See the LICENSE file for details.

## Acknowledgments

- PyAudio/sounddevice community for audio capture libraries
- Signal processing algorithms based on established DSP techniques
- Open-source community for Python scientific computing tools

## Contact & Support

For questions, issues, or suggestions:
- **GitHub Issues**: https://github.com/ddicostanzo/panel_qc/issues
- **Repository**: https://github.com/ddicostanzo/panel_qc

## Disclaimer

This software is provided "as is" without warranty of any kind. The authors and contributors are not responsible for any damage, injury, or loss resulting from the use of this software. Always consult qualified professionals for electrical work and safety assessments.

## Future Enhancements

Potential future features may include:

- Machine learning-based classification of different buzzing types
- Integration with IoT platforms for remote alerts
- Mobile application for portable monitoring
- Historical data analysis and trending
- Integration with thermal imaging data
- Multi-channel audio analysis for large electrical installations

## Version History

Refer to the repository's commit history and releases page for detailed version information.

---

**Last Updated**: November 2025  
**Maintainer**: ddicostanzo  
**Status**: Active Development

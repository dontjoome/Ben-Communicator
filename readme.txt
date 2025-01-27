# Ben's Accessibility Software

## Overview
This project is designed to enhance accessibility for individuals with specific physical challenges, such as Ben, who has TUBB4a-related Leukodystrophy. Ben uses a two-button system for navigation and communication. This software integrates with his setup to:

1. Provide scan-and-select capabilities.
2. Open specific links to favorite shows.
3. Include a menu for common phrases for easier communication.
4. Track and update the URLs of shows Ben watches dynamically, ensuring seamless continuation from the last episode.
5. Offer emergency, settings, communication, and entertainment functions.
6. Added the keyboard.py to open in the Communication Menu (opens and then closes Comm-v8 - when closing keyboard, it will reopen Comm-v8 provided it's in the same directory)

## Features
- **Emergency Function**: Triggers an alert for immediate assistance.
- **Scan-and-Select Navigation**: Allows Ben to use two buttons attached to his headrest to interact with the software.
- **Settings Controls**:
  - Volume Up/Down
  - Sleep Timer (60 minutes)
  - Cancel Sleep Timer
  - Turn Display Off
  - Lock Computer
  - Restart Computer
  - Shut Down Computer
- **Customizable Phrase Menu**: Preloaded with around 50 common phrases for quick communication.
- **Dynamic Show Tracking**: Automatically saves the last viewed URL for each show when Chrome is closed, enabling easy resumption.
- **Chrome Auto-Close**: Chrome automatically minimizes or closes to enhance focus. To close Chrome using the buttons, press `Enter-Space-Space`.
- **On-Screen Keyboard**: Includes functionality for spelling words and text-to-speech output.
- **Entertainment Menu**: Provides access to streaming shows, live streams, and coming-soon features like games and audiobooks.

## Future Enhancements
1. **Predictive Text Integration**: Adding OpenAI or similar functionality for contextual predictive text to enhance communication.
2. **Games**:
   - Tic Tac Toe designed for two-button operation.
   - AI-driven, choice-based storytelling game (e.g., a fantasy adventure where Ben can collect items and make decisions, all narrated with text-to-speech).
3. **Virtual Pet**: A "Tamagotchi"-style pet that Ben can feed and interact with, potentially engaging with others as well.

## Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/ben-accessibility-software.git
   ```
2. Navigate to the project directory:
   ```bash
   cd ben-accessibility-software
   ```
3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python main.py
   ```

## Usage
1. **Starting the Software**:
   - Connect Ben's two-button device to the computer.
   - Launch the application using `python main.py`.
2. **Navigating the Interface**:
   - Use the `Scan` button to highlight options.
   - Use the `Select` button to confirm a choice.
3. **Opening Shows**:
   - Navigate to the "Favorite Shows" menu.
   - Select a show to resume from the last saved URL.
4. **Using Common Phrases**:
   - Access the "Phrases" menu.
   - Select a phrase to display or speak it using text-to-speech.

## Configuration
- **Phrases Menu**: Update `phrases.json` to add or modify common phrases.
- **Shows List**: Update `shows.json` to add new shows and their initial URLs.
- **Button Mapping**: Modify `settings.py` to configure input mappings for the two-button device.

## Dependencies
- Python 3.8+
- PyAutoGUI
- PyTTSx3 (Text-to-Speech)
- Flask (Optional for Web Interface)

## Contributing
Contributions are welcome! Please fork this repository and submit a pull request with your changes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments
Special thanks to Ben and his family for inspiring this project and providing valuable feedback for its development.

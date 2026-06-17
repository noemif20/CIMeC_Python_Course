**Data manager user guide
**
Purpose: This script helps organize experimental video recordings and metadata files.

The script will:

validate recording filenames;
propose corrections for predictable filename formatting errors;
copy recordings from a source folder to a destination folder;
create metadata YAML files when missing;
validate existing metadata files;
report any detected errors or inconsistencies.

The script never guesses missing metadata values and will ask the user for any required information.

Required Filename Format: All recordings must follow the format: sub-fxxxx_expType-xxxx_trialn-x_date-YYYYmmdd_recording.mp4

Examples:

sub-f0007_expType-2choice_trialn-1_date-20260421_recording.mp4

sub-f0788_expType-socialpreference_trialn-2_date-20260429_recording.mp4

sub-f0782_expType-mirrortest_trialn-1_date-20260422_recording.mp4

sub-f0608_expType-openField_trialn-1_date-20251212_recording.mp4

Supported Experiment Types: The following experiment types are supported:

2choice
openField
mirrortest
socialpreference

Before Running the Script: Create a source folder containing the recording files. Create a destination folder where processed files and metadata will be stored. Finally, ensure Python is installed.
Install PyYAML if necessary: pip install pyyaml


Running the Script

Open a terminal (Command Prompt, PowerShell, Terminal, etc.).

Navigate to the folder containing the script: cd path/to/script

Run: python data_manager.py --source PATH_TO_SOURCE_FOLDER --destination PATH_TO_DESTINATION_FOLDER

Example:

python data_manager.py --source C:\Data\RawVideos --destination C:\Data\ProcessedVideos

Interactive Metadata Entry: For each recording, the script displays the recording being processed and requests any required metadata that cannot be obtained from the filename.

Depending on the experiment type, the script may ask for:

apparatusType

Allowed values:

box
well

contrast (2choice only)

Allowed values:

1vs2
1vs3
1vs4
2vs4
2vs6
2vs6sf

mirrorPos (mirrortest only)

Allowed values:

top
bottom

stimSides (2choice and socialpreference)

Enter:

left stimulus value
right stimulus value

Example:

Left stimulus: 4
Right stimulus: 1

Filename Corrections: If the script detects a predictable filename formatting error, it will propose a correction and request approval.

Example:

Original:
sub-f0007__expType-2choice_trialn-1_date-20260421.mp4

Proposed:
sub-f0007_expType-2choice_trialn-1_date-20260421_recording.mp4

Apply correction? [y/N]

The correction is applied only after explicit user approval.

Generated Metadata Files: For every recording, a metadata file is created using the same basename.

Example:

Recording:

sub-f0007_expType-2choice_trialn-1_date-20260421_recording.mp4

Metadata:

sub-f0007_expType-2choice_trialn-1_date-20260421_metadata.yml

Existing Files

Existing Recording in Destination Folder: If a recording already exists in the destination folder the file is not overwritten; the copy operation is skipped and a message is displayed.

Existing Metadata File: If a metadata file already exists the file is validated; validation results are reported; valid metadata files are left unchanged.

Validation Performed

The script validates:

filename format;
subject identifier format;
experiment type;
trial number;
date format;
YAML syntax;
required YAML fields;
allowed metadata values;
consistency between filename and metadata file;
experiment-specific metadata requirements.

Log File: All actions, warnings, and errors are recorded in: processing.log located in the destination folder.

Important Notes

The script does not guess missing metadata.
The script does not infer metadata from incomplete filenames.
The script does not overwrite existing recordings.
Filename corrections require user approval.
Ambiguous filenames must be corrected manually.
Metadata entered by the user is assumed to be correct.
Original recordings are preserved unless the user explicitly approves a filename correction.

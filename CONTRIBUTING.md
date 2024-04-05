# Contributing to the project
Thank you for taking the time to contribute!

These are the main ways to contribute:
- [Reporting bugs](#reporting-bugs)
- [Suggesting enhancements](#suggesting-enhancements)
- [Protocol reverse-engineering](#protocol-reverse-engineering)
- [Adding new features to the script](#adding-new-features)
- [Translating field names](#translating-field-names)

## Reporting bugs
If you find any problem with the script, you can open an issue. Do not forget to mention the script version, your inverter model and connection mode (station or AP) if relevant.

## Suggesting enhancements
Do you think something could work differently? You are welcome to suggest any changes by opening an issue.

## Protocol reverse-engineering
If you do not know Python or you do not want to contribute any code, you can help with reverse-engineering the inverter's protocol. Check for data and values that are available in the app and not in the script and try to locate them in the captured packets. The process is documented in the relevant files in the docs folder. *Note: nowadays majority of the protocol is already reverse-engineered. There are still some things that may be useful to find out. Contact the main developer to get an info about what remains to be done.*

## Adding new features
You are always welcome to contribute new features. Please open an issue so others know you are working on the problem, fork the project, create a branch with a descriptive name and after your code is ready, open a pull request. Please describe the changes well in the pull request, so it can be merged as soon as possible.

## Translating field names
If your preffered language is not supported, do not worry, adding support is very easy. Just copy the English translation file (`en.csv` in `src/sermatec_inverter/translations` folder), name the new file according to [ISO 639 two-letter code](https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes) and translate values in the second column!
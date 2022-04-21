# Final Fantasy Brave Exvius Data Dump
A repo of Final Fantasy Brave Exvius asset dump

## How to find units
In the `data.json` file, search for the name of the unit you're looking for. Copy the associated **Unit ID** and search the repository for that ID.
`data.json` will be updated weekly with the current released units on the Global (GL) server. Japan (JP) server units are present in the datamine.

## How to convert the PNGs into animated sprites
* Note: Requires [nodejs](https://nodejs.org/en/)

Use the [FFBE Sprite Sheet Assembler](https://github.com/dsxragnarok/FFBE-sprite-sheet-assembler) tool by dsxragnarok.

Download the sprite sheet from the `unit_animated` folder and the corresponding .csv file from `unit_animated_csv`. Follow the instructions from the Sprite Sheet Assembler.

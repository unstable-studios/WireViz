# Change Log

## [0.5.0](https://github.com/unstable-studios/WireViz/compare/v0.4.1...v0.5.0) (2026-08-20)


### Features

* add --merge to build one harness from several files ([c155663](https://github.com/unstable-studios/WireViz/commit/c155663762e9f2cbf38c50aa91809627ca453d68))
* add --strict to reject silently dropped input ([5400a27](https://github.com/unstable-studios/WireViz/commit/5400a2704863248185af989aed8871115be26b62))
* add options.rankdir, and make port compass points follow it ([1d70f73](https://github.com/unstable-studios/WireViz/commit/1d70f73be2208548e1a77e4f06c6a7c58ea30523))
* **html:** interactive diagrams — pan/zoom, net tracing, BOM linkage ([#17](https://github.com/unstable-studios/WireViz/issues/17)) ([1690b63](https://github.com/unstable-studios/WireViz/commit/1690b63c487469f5cc0e9cb3c47cc83570b9f115))
* **html:** print stylesheet and dark mode for the simple template ([#24](https://github.com/unstable-studios/WireViz/issues/24)) ([c80b2a6](https://github.com/unstable-studios/WireViz/commit/c80b2a6189ef7f7861ea58fc9c987f436f8f2ef7))
* **html:** widen the wire hover target ([#22](https://github.com/unstable-studios/WireViz/issues/22)) ([84b4833](https://github.com/unstable-studios/WireViz/commit/84b48335a3d15bac6574cadda036c3975b6e7345))
* **layout:** add mate_labels option to annotate mate arrows ([#25](https://github.com/unstable-studios/WireViz/issues/25)) ([68aaf71](https://github.com/unstable-studios/WireViz/commit/68aaf714c097f18701db78c3fd478b6f0ba430ad))
* **layout:** add note_wrap option to wrap long notes at render time ([#34](https://github.com/unstable-studios/WireViz/issues/34)) ([e26479e](https://github.com/unstable-studios/WireViz/commit/e26479e2c74f42a6037fd25a2a47fb65351e2c15))
* **layout:** add options.order to pin down node stacking within a rank ([#23](https://github.com/unstable-studios/WireViz/issues/23)) ([762d6f9](https://github.com/unstable-studios/WireViz/commit/762d6f9abf9605168db3c65a94c2b82cbebc1321))
* **layout:** add options.sort_wires to untangle wire-row crossings ([#16](https://github.com/unstable-studios/WireViz/issues/16)) ([5dd1ab7](https://github.com/unstable-studios/WireViz/commit/5dd1ab7c149ee66a38f814c3fa855bda347feb4b))
* **layout:** add shield_style option to distinguish shields from black wires ([#27](https://github.com/unstable-studios/WireViz/issues/27)) ([e3d83c1](https://github.com/unstable-studios/WireViz/commit/e3d83c1a328767fa7e56f59f2015968a7dd96ef8)), closes [#9](https://github.com/unstable-studios/WireViz/issues/9)
* **layout:** add wirelabel_detail option to abbreviate in-cable labels ([#26](https://github.com/unstable-studios/WireViz/issues/26)) ([91f4a8b](https://github.com/unstable-studios/WireViz/commit/91f4a8beb40d6579bdf00625963d4ace2b8b5402)), closes [#11](https://github.com/unstable-studios/WireViz/issues/11)
* **layout:** orthogonal wire routing + flush TB colour bars ([#37](https://github.com/unstable-studios/WireViz/issues/37)) ([29102ce](https://github.com/unstable-studios/WireViz/commit/29102ce65630a0af12a721d1a60e3cc0eae7ffa7))
* **layout:** transpose node tables so rankdir TB renders correctly ([#18](https://github.com/unstable-studios/WireViz/issues/18)) ([a6a6bec](https://github.com/unstable-studios/WireViz/commit/a6a6bec7e6675a81587cd2378a0f38de35d17e85))
* **options:** expose ranksep, nodesep, and wire_thickness ([#15](https://github.com/unstable-studios/WireViz/issues/15)) ([b04978b](https://github.com/unstable-studios/WireViz/commit/b04978b476ca3e56bc5127622460c3e977629a36))
* **routing:** draw junction dots where same-net wires meet ([#41](https://github.com/unstable-studios/WireViz/issues/41)) ([6b584a1](https://github.com/unstable-studios/WireViz/commit/6b584a170088df685d1193d19c80deffb7389f1b))
* **routing:** make the orthogonal router avoid node boxes ([#39](https://github.com/unstable-studios/WireViz/issues/39)) ([1f18386](https://github.com/unstable-studios/WireViz/commit/1f183863014262ca9b58d2112c6a671ddbe9b3d4))
* **sheets:** multi-sheet interactive HTML output ([#30](https://github.com/unstable-studios/WireViz/issues/30)) ([1f4dd3e](https://github.com/unstable-studios/WireViz/commit/1f4dd3e33c61d98e3d1833ece48ff65c2d9b709c)), closes [#14](https://github.com/unstable-studios/WireViz/issues/14)
* **sheets:** per-sheet file outputs and sheet metadata ([#29](https://github.com/unstable-studios/WireViz/issues/29)) ([6b32d73](https://github.com/unstable-studios/WireViz/commit/6b32d73569f21b5fbba00cacc803f54bf06d8353))
* **sheets:** split a harness into per-sheet sub-harnesses ([#28](https://github.com/unstable-studios/WireViz/issues/28)) ([0665d63](https://github.com/unstable-studios/WireViz/commit/0665d632c2009c5f25c4826039a4ae4853310759))


### Bug Fixes

* **html:** stop text selection while panning the interactive viewer ([#40](https://github.com/unstable-studios/WireViz/issues/40)) ([7bfe931](https://github.com/unstable-studios/WireViz/commit/7bfe9313b0035d4ffec928cf72b0e7b156924cf4))


### Documentation

* record that TB is not finished, and why ([fa2700c](https://github.com/unstable-studios/WireViz/commit/fa2700c1a82b27798a11837952f582680583ac82))

## [0.4.1] (2024-07-13)

### Improvements to help reported issues

- Print Python & OS versions when raising unexpected OSError related to #346 & #392 (bugfixes below)
- Explain unexpeced top-level type ([#342](https://github.com/wireviz/WireViz/issues/342), [#383](https://github.com/wireviz/WireViz/pull/383))
- Add non-empty label to reduce over-sized loops ([#286](https://github.com/wireviz/WireViz/issues/286), [#381](https://github.com/wireviz/WireViz/pull/381))
- Improve placeholder name consistency ([#377](https://github.com/wireviz/WireViz/issues/377), [#380](https://github.com/wireviz/WireViz/pull/380))
- Add work-around for Graphviz SVG bug ([#175](https://github.com/wireviz/WireViz/issues/175), [#371](https://github.com/wireviz/WireViz/pull/371))

### Bugfixes

- Avoid ResourceWarning: unclosed file ([#309 (comment)](https://github.com/wireviz/WireViz/pull/309#issuecomment-2170988381), [#395](https://github.com/wireviz/WireViz/pull/395))
- Catch ValueError and OSError(errno=None) ([#318 (review)](https://github.com/wireviz/WireViz/pull/318#pullrequestreview-1457016602), [#391](https://github.com/wireviz/WireViz/issues/391), [#392](https://github.com/wireviz/WireViz/pull/392))
- Add minor missing doc entry ([#186 (comment)](https://github.com/wireviz/WireViz/pull/186#issuecomment-2139037434), [#186 (comment)](https://github.com/wireviz/WireViz/pull/186#issuecomment-2155032522))
- Avoid Graphviz error when hiding all pins ([#257](https://github.com/wireviz/WireViz/issues/257), [#375](https://github.com/wireviz/WireViz/pull/375))
- Avoid decimal point and trailing zero for integer BOM quantities ([#340](https://github.com/wireviz/WireViz/issues/340), [#374](https://github.com/wireviz/WireViz/pull/374))
- Update project URL references ([#316 (comment)](https://github.com/wireviz/WireViz/issues/316#issuecomment-1568748914), [#364](https://github.com/wireviz/WireViz/pull/364))
- Add missing import of embed_svg_images ([#363](https://github.com/wireviz/WireViz/pull/363))
- Use correct default title ([#360](https://github.com/wireviz/WireViz/issues/360), [#361](https://github.com/wireviz/WireViz/pull/361))
- Fix bugs in mate processing ([#355](https://github.com/wireviz/WireViz/issues/355), [#358](https://github.com/wireviz/WireViz/pull/358))
- Include missing files in published package ([#345](https://github.com/wireviz/WireViz/issues/345), [#347](https://github.com/wireviz/WireViz/pull/347)) 
- Catch OSError(errno=EINVAL) ([#344](https://github.com/wireviz/WireViz/issues/344), [#346](https://github.com/wireviz/WireViz/pull/346))


## [0.4](https://github.com/wireviz/WireViz/tree/v0.4) (2024-05-12)

### Backward-incompatible changes
- New syntax for autogenerated components ([#184](https://github.com/wireviz/WireViz/issues/184), [#186](https://github.com/wireviz/WireViz/pull/186))
  - Components that are not referenced in any connection set will not be rendered. Instead, a warning will be output in the console. ([#328](https://github.com/wireviz/WireViz/issues/328), [#332](https://github.com/wireviz/WireViz/pull/332))
- New command line interface ([#244](https://github.com/wireviz/WireViz/pull/244)). Run `wireviz --help` for details 
  - The path specified with the `-o`/`--output-dir` option no longer includes the filename (without extension) of the generated files. Use the `-O`/`--output-name` option to specify a different filename for the generated files.
- The `.gv` file is no longer included as a default output format (only as an intermediate file during processing) unless specified with the new `-f` option described below.

### New features

- Allow mates between connectors ([#134](https://github.com/wireviz/WireViz/issues/134), [#186](https://github.com/wireviz/WireViz/pull/186))
- Improve technical drawing output ([#74](https://github.com/wireviz/WireViz/pull/74), [#32](https://github.com/wireviz/WireViz/issues/32), [#239](https://github.com/wireviz/WireViz/pull/239))
- Embed images in SVG output ([#189](https://github.com/wireviz/WireViz/pull/189))
- Add ability to choose output formats using the `-f`/`--format` command line option ([#60](https://github.com/wireviz/WireViz/issues/60))
- Add option to multiply additional component quantity by number of unpopulated positions on connector ([#298](https://github.com/wireviz/WireViz/pull/298))

### Misc. fixes
- Use `isort` and `black` for cleaner code and easier merging ([#248](https://github.com/wireviz/WireViz/pull/248))
- Code improvements ([#246](https://github.com/wireviz/WireViz/pull/246), [#250](https://github.com/wireviz/WireViz/pull/250))
- Bug fixes ([#264](https://github.com/wireviz/WireViz/pull/264), [#318](https://github.com/wireviz/WireViz/pull/318))
- Minor adjustments ([#256](https://github.com/wireviz/WireViz/pull/256))


## [0.3.2](https://github.com/wireviz/WireViz/tree/v0.3.2) (2021-11-27)

### Hotfix

- Adjust GraphViz generation code for compatibility with v0.18 of the `graphviz` Python package ([#258](https://github.com/wireviz/WireViz/issues/258), [#261](https://github.com/wireviz/WireViz/pull/261))


## [0.3.1](https://github.com/wireviz/WireViz/tree/v0.3.1) (2021-10-25)

### Hotfix

- Assign generic harness title when using WireViz as a module and not specifying an output file name ([#253](https://github.com/wireviz/WireViz/issues/253), [#254](https://github.com/wireviz/WireViz/pull/254))


## [0.3](https://github.com/wireviz/WireViz/tree/v0.3) (2021-10-11)

### New features

- Allow referencing a cable's/bundle's wires by color or by label ([#70](https://github.com/wireviz/WireViz/issues/70), [#169](https://github.com/wireviz/WireViz/issues/169), [#193](https://github.com/wireviz/WireViz/issues/193), [#194](https://github.com/wireviz/WireViz/pull/194))
- Allow additional BOM items within components ([#50](https://github.com/wireviz/WireViz/issues/50), [#115](https://github.com/wireviz/WireViz/pull/115))
- Add support for length units in cables and wires ([#7](https://github.com/wireviz/WireViz/issues/7), [#196](https://github.com/wireviz/WireViz/pull/196) (with work from [#161](https://github.com/wireviz/WireViz/pull/161), [#162](https://github.com/wireviz/WireViz/pull/162), [#171](https://github.com/wireviz/WireViz/pull/171)), [#198](https://github.com/wireviz/WireViz/pull/198), [#205](https://github.com/wireviz/WireViz/issues/205). [#206](https://github.com/wireviz/WireViz/pull/206))
- Add option to define connector pin colors ([#53](https://github.com/wireviz/WireViz/issues/53), [#141](https://github.com/wireviz/WireViz/pull/141))
- Remove HTML links from the input attributes ([#164](https://github.com/wireviz/WireViz/pull/164))
- Add harness metadata section ([#158](https://github.com/wireviz/WireViz/issues/158), [#214](https://github.com/wireviz/WireViz/pull/214))
- Add support for supplier and supplier part number information ([#240](https://github.com/wireviz/WireViz/issues/240), [#241](https://github.com/wireviz/WireViz/pull/241/))
- Add graph rendering options (background colors, fontname, color name display style, ...) ([#158](https://github.com/wireviz/WireViz/issues/158), [#214](https://github.com/wireviz/WireViz/pull/214))
- Add support for background colors for cables and connectors, as well as for some individual cells ([#210](https://github.com/wireviz/WireViz/issues/210), [#219](https://github.com/wireviz/WireViz/pull/219))
- Add optional tweaking of the .gv output ([#215](https://github.com/wireviz/WireViz/pull/215)) (experimental)

### Misc. fixes

- Remove case-sensitivity issues with pin names and labels ([#160](https://github.com/wireviz/WireViz/issues/160), [#229](https://github.com/wireviz/WireViz/pull/229))
- Improve type hinting ([#156](https://github.com/wireviz/WireViz/issues/156), [#163](https://github.com/wireviz/WireViz/pull/163))
- Move BOM management and HTML functions to separate modules ([#151](https://github.com/wireviz/WireViz/issues/151), [#192](https://github.com/wireviz/WireViz/pull/192))
- Simplify BOM code ([#197](https://github.com/wireviz/WireViz/pull/197))
- Bug fixes ([#218](https://github.com/wireviz/WireViz/pull/218), [#221](https://github.com/wireviz/WireViz/pull/221))

### Known issues

- Including images in the harness may lead to issues in the following cases: ([#189](https://github.com/wireviz/WireViz/pull/189), [#220](https://github.com/wireviz/WireViz/issues/220))
  - When using the `-o`/`--output_file` CLI option, specifying an output path in a different directory from the input file
  - When using the `--prepend-file` CLI option, specifying a prepend file in a different directory from the mail input file


## [0.2](https://github.com/wireviz/WireViz/tree/v0.2) (2020-10-17)

### Backward incompatible changes

- Change names of connector attributes ([#77](https://github.com/wireviz/WireViz/issues/77), [#105](https://github.com/wireviz/WireViz/pull/105))
  - `pinnumbers` is now `pins`
  - `pinout` is now `pinlabels`
- Remove ferrules as a separate connector type ([#78](https://github.com/wireviz/WireViz/issues/78), [#102](https://github.com/wireviz/WireViz/pull/102))
  - Simple connectors like ferrules are now defined using the `style: simple` attribute
- Change the way loops are defined ([#79](https://github.com/wireviz/WireViz/issues/79), [#75](https://github.com/wireviz/WireViz/pull/75))
  - Wires looping between two pins of the same connector are now handled via the connector's `loops` attribute.

See the [syntax description](syntax.md) for details.

### New features

- Add bidirectional AWG/mm2 conversion ([#40](https://github.com/wireviz/WireViz/issues/40), [#41](https://github.com/wireviz/WireViz/pull/41))
- Add support for part numbers ([#11](https://github.com/wireviz/WireViz/pull/11), [#114](https://github.com/wireviz/WireViz/issues/114), [#121](https://github.com/wireviz/WireViz/pull/121))
- Add support for multicolored wires ([#12](https://github.com/wireviz/WireViz/issues/12), [#17](https://github.com/wireviz/WireViz/pull/17), [#96](https://github.com/wireviz/WireViz/pull/96), [#131](https://github.com/wireviz/WireViz/issues/131), [#132](https://github.com/wireviz/WireViz/pull/132))
- Add support for images ([#27](https://github.com/wireviz/WireViz/issues/27), [#153](https://github.com/wireviz/WireViz/pull/153))
- Add ability to export data directly to other programs ([#55](https://github.com/wireviz/WireViz/pull/55))
- Add support for line breaks in various fields ([#49](https://github.com/wireviz/WireViz/issues/49), [#64](https://github.com/wireviz/WireViz/pull/64))
- Allow using connector pin names to define connections ([#72](https://github.com/wireviz/WireViz/issues/72), [#139](https://github.com/wireviz/WireViz/issues/139), [#140](https://github.com/wireviz/WireViz/pull/140))
- Make defining connection sets easier and more flexible ([#67](https://github.com/wireviz/WireViz/issues/67), [#75](https://github.com/wireviz/WireViz/pull/75))
- Add new command line options ([#167](https://github.com/wireviz/WireViz/issues/167), [#173](https://github.com/wireviz/WireViz/pull/173))
- Add new features to `build_examples.py` ([#118](https://github.com/wireviz/WireViz/pull/118))
- Add new colors ([#103](https://github.com/wireviz/WireViz/pull/103), [#113](https://github.com/wireviz/WireViz/pull/113), [#144](https://github.com/wireviz/WireViz/issues/144), [#145](https://github.com/wireviz/WireViz/pull/145))
- Improve documentation ([#107](https://github.com/wireviz/WireViz/issues/107), [#111](https://github.com/wireviz/WireViz/pull/111))

### Misc. fixes

- Improve BOM generation
- Add various input sanity checks
- Improve HTML output ([#66](https://github.com/wireviz/WireViz/issues/66), [#136](https://github.com/wireviz/WireViz/pull/136), [#95](https://github.com/wireviz/WireViz/pull/95), [#177](https://github.com/wireviz/WireViz/pull/177))
- Fix node rendering bug ([#69](https://github.com/wireviz/WireViz/issues/69), [#104](https://github.com/wireviz/WireViz/pull/104))
- Improve shield rendering ([#125](https://github.com/wireviz/WireViz/issues/125), [#126](https://github.com/wireviz/WireViz/pull/126))
- Add GitHub Linguist overrides ([#146](https://github.com/wireviz/WireViz/issues/146), [#154](https://github.com/wireviz/WireViz/pull/154))


## [0.1](https://github.com/wireviz/WireViz/tree/v0.1) (2020-06-29)

- Initial release

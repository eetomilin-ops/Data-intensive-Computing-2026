# Token dictionary split report

Source: Task1/presentation/output.txt
Date: 2026-04-27

## Scope
This report groups non-standard tokens from the output dictionary into practical buckets for review:
1. high-confidence misspellings or malformed words
2. abbreviations, slang, and domain shorthand
3. likely proper nouns, brands, and product names

Note: A strict English dictionary check flags many valid domain terms, names, and brands. This split is intended for presentation-quality interpretation.

## 1) High-confidence misspellings or malformed words
- accessorie
- kitche
- garde
- supplie
- faotd
- apos
- hea
- quot

## 2) Abbreviations, slang, or shorthand (non-dictionary but context-valid)
- yr
- edc
- daw
- bbs
- mp
- gps
- obd
- rv
- tv
- dvd
- blu
- usb
- hdmi
- lcd
- spf
- bpm

## 3) Likely proper nouns, brands, or product names (dictionary false positives)
- gameloft
- mahjong
- otterbox
- weathertech
- playtex
- nuk
- evenflo
- medela
- chicco
- boppy
- britax
- norelco
- sonicare
- gillette
- dewalt
- makita
- bosch
- dremel
- streamlight
- kitchenaid
- cuisinart
- dyson
- weber
- husqvarna
- toro
- fiskars
- frontline
- furminator
- greenies
- leapfrog
- playmobil
- hasbro
- ravensburger
- melissa
- doug

## Summary
The output contains a small set of clear malformed tokens and many non-dictionary tokens that are expected in review corpora (brands, abbreviations, and product jargon). This is normal for discriminative feature extraction on noisy real-world text.
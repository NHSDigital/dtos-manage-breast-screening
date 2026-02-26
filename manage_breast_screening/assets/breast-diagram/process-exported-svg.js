//
// Processes the exported SVG from Illustrator to add required data attributes
// and clean up for use in the breast features component.
//
// Usage: node process-exported-svg.js <input-file.svg>
// Output: Creates <input-file>-processed.svg in the same directory

import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import {
  extname,
  basename as _basename,
  dirname as _dirname,
  join
} from 'node:path'

import { processSvg } from './breast-diagram.js'

function cli() {
  // Get input file from command line
  const inputFile = process.argv[2]

  if (!inputFile) {
    console.error('Usage: node process-exported-svg.js <input-file.svg>')
    process.exitCode = 1
    return
  }

  if (!existsSync(inputFile)) {
    console.error(`File not found: ${inputFile}`)
    process.exitCode = 1
    return
  }

  // Read the SVG file
  const svgContent = readFileSync(inputFile, 'utf8')

  // Process the SVG
  const processedSvg = processSvg(svgContent, inputFile)

  // Generate output filename
  const ext = extname(inputFile)
  const basename = _basename(inputFile, ext)
  const dirname = _dirname(inputFile)
  const outputFile = join(dirname, `${basename}-processed${ext}`)

  // Write the processed SVG
  writeFileSync(outputFile, processedSvg)

  console.log(`Processed SVG written to: ${outputFile}`)
}

cli()

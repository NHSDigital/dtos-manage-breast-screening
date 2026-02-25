const { processSvg } = require('./process-exported-svg.cjs')

const testSVG = `<?xml version="1.0" encoding="UTF-8"?>
<svg id="Breast_diagram_to_export" data-name="Breast diagram to export" xmlns="http://www.w3.org/2000/svg" width="800" height="400" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 800 400">
  <defs>
    <clipPath id="clippath">
      <rect id="container_outline" data-name="container outline" width="800" height="400" fill="none"/>
    </clipPath>
  </defs>
  <g id="left">
    <path id="upper" data-name="upper" d="M417.32,0v165.56l124.46,15.9,2.42,2.42c-5,5.01-7.6,12.26-6.38,19.77.79,4.92,3.11,9.21,6.38,12.47l2.41,2.42,14.88,116.46,125.75-16.06c.77-15,2.88-26.92,6.3-36.5-.05-27.65-5.53-54.03-15.43-78.12l-101.75,14.22L562,65l-42.36-5.93L545.46,0H417.32Z" fill="none"/>
    <path id="lower" data-name="lower" d="M400,234.02v143.98h160.32v-23.33c-43.13,0-76.02-10.35-101.94-32.09l21.62-28.95c-28.17-21.35-44.51-52.66-53.28-81.7l-121.19,15.48h-.01l-2.41-2.42c3.27-3.26,5.59-7.55,6.38-12.47,1.22-7.51-1.38-14.76-6.38-19.77l2.41-2.42,14.88,116.46c5.95-1.65,11.54-3.62,16.76-5.79.04-.02.09-.04.13-.06,23-9.59,38.57-23.02,44.27-29.66.42-.5,24.86-26.41,39.1-66.67.21-.6.43-1.21.63-1.82l9.34,4.27,95.73,43.87V125.45l-25.8-38.39c-31.82,5.85-53.22,13.69-63.28,41.84-3.42,9.58-5.53,21.5-6.3,36.5-.21,4.23-.32,8.72-.32,13.46,0,19.95-3.83,38.35-9.37,54.51Z" fill="none"/>
  </g>
  <g id="right">
    <path id="upper-2" data-name="upper" d="M382.68,0v165.56l-124.46,15.9-2.42,2.42c5,5.01,7.6,12.26,6.38,19.77-.79,4.92-3.11,9.21-6.38,12.47l-2.41,2.42L238.51,334l-125.75-16.06c-.77-15-2.88-26.92-6.3-36.5.05-27.65,5.53-54.03,15.43-78.12l101.75,14.22L238,65l42.36-5.93L254.54,0H382.68Z" fill="none"/>
    <path id="lower-2" data-name="lower" d="M400,234.02v143.98h-160.32v-23.33c43.13,0,76.02-10.35,101.94-32.09l-21.62-28.95c28.17-21.35,44.51-52.66,53.28-81.7l-121.19,15.48h.01l2.41-2.42c-3.27-3.26-5.59-7.55-6.38-12.47-1.22-7.51,1.38-14.76,6.38-19.77l-2.41-2.42L236.92,308.66c-5.95-1.65-11.54-3.62-16.76-5.79-.04-.02-.09-.04-.13-.06-23-9.59-38.57-23.02-44.27-29.66-.42-.5-24.86-26.41-39.1-66.67-.21-.6-.43-1.21-.63-1.82l-9.34,4.27L30.96,252.8V125.45l25.8-38.39c31.82,5.85,53.22,13.69,63.28,41.84,3.42,9.58,5.53,21.5,6.3,36.5.21,4.23.32,8.72.32,13.46,0,19.95,3.83,38.35,9.37,54.51Z" fill="none"/>
  </g>
  <g id="diagram">
    <g id="Clipped_breast_diagram" data-name="Clipped breast diagram">
      <g clip-path="url(#clippath)">
        <g id="left-2" data-name="left">
          <path id="Breast_outline" data-name="Breast outline" d="M808.48,138.1l-34.3-51.04c-45.7,8.4-69.9,20.9-69.9,91.8s-48.5,122.3-49.1,123c-12.1,14.1-68.7,58.8-146.3,32.4-77.7-26.4-97.1-115.4-97.1-155.5" fill="none" stroke="#212b32" stroke-linecap="round" stroke-width="3"/>
          <circle id="Nipple_outline" data-name="Nipple outline" cx="560.31" cy="200" r="22.8" fill="none" stroke="#212b32" stroke-linecap="round" stroke-miterlimit="4" stroke-width="3"/>
        </g>
        <g id="right-2" data-name="right">
          <path id="Breast_outline-2" data-name="Breast outline" d="M-8.5,138.1l34.3-51.04c45.7,8.4,69.9,20.9,69.9,91.8s48.5,122.3,49.1,123c12.1,14.1,68.7,58.8,146.3,32.4,77.7-26.4,97.1-115.4,97.1-155.5" fill="none" stroke="#212b32" stroke-linecap="round" stroke-width="3"/>
          <circle id="Nipple_outline-2" data-name="Nipple outline" cx="239.68" cy="200" r="22.8" fill="none" stroke="#212b32" stroke-linecap="round" stroke-miterlimit="4" stroke-width="3"/>
        </g>
      </g>
    </g>
  </g>
</svg>
`

const testSVGProcessed = `<!-- Source: test -->
<!-- Processed by process-exported-svg.js - do not edit manually -->

<svg class="app-breast-diagram__svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400">
  <defs>
    <clipPath id="clippath">
      <rect width="800" height="400" fill="none"/>
    </clipPath>
  </defs>
  <g class="app-breast-diagram__regions">
    <g class="app-breast-diagram__regions-left">
      <path class="left_upper" d="M417.32,0v165.56l124.46,15.9,2.42,2.42c-5,5.01-7.6,12.26-6.38,19.77.79,4.92,3.11,9.21,6.38,12.47l2.41,2.42,14.88,116.46,125.75-16.06c.77-15,2.88-26.92,6.3-36.5-.05-27.65-5.53-54.03-15.43-78.12l-101.75,14.22L562,65l-42.36-5.93L545.46,0H417.32Z" fill="none">
        <title>left upper</title>
      </path>
      <path class="left_lower" d="M400,234.02v143.98h160.32v-23.33c-43.13,0-76.02-10.35-101.94-32.09l21.62-28.95c-28.17-21.35-44.51-52.66-53.28-81.7l-121.19,15.48h-.01l-2.41-2.42c3.27-3.26,5.59-7.55,6.38-12.47,1.22-7.51-1.38-14.76-6.38-19.77l2.41-2.42,14.88,116.46c5.95-1.65,11.54-3.62,16.76-5.79.04-.02.09-.04.13-.06,23-9.59,38.57-23.02,44.27-29.66.42-.5,24.86-26.41,39.1-66.67.21-.6.43-1.21.63-1.82l9.34,4.27,95.73,43.87V125.45l-25.8-38.39c-31.82,5.85-53.22,13.69-63.28,41.84-3.42,9.58-5.53,21.5-6.3,36.5-.21,4.23-.32,8.72-.32,13.46,0,19.95-3.83,38.35-9.37,54.51Z" fill="none">
        <title>left lower</title>
      </path>
    </g>
    <g class="app-breast-diagram__regions-right">
      <path class="right_upper" d="M382.68,0v165.56l-124.46,15.9-2.42,2.42c5,5.01,7.6,12.26,6.38,19.77-.79,4.92-3.11,9.21-6.38,12.47l-2.41,2.42L238.51,334l-125.75-16.06c-.77-15-2.88-26.92-6.3-36.5.05-27.65,5.53-54.03,15.43-78.12l101.75,14.22L238,65l42.36-5.93L254.54,0H382.68Z" fill="none">
        <title>right upper</title>
      </path>
      <path class="right_lower" d="M400,234.02v143.98h-160.32v-23.33c43.13,0,76.02-10.35,101.94-32.09l-21.62-28.95c28.17-21.35,44.51-52.66,53.28-81.7l-121.19,15.48h.01l2.41-2.42c-3.27-3.26-5.59-7.55-6.38-12.47-1.22-7.51,1.38-14.76,6.38-19.77l-2.41-2.42L236.92,308.66c-5.95-1.65-11.54-3.62-16.76-5.79-.04-.02-.09-.04-.13-.06-23-9.59-38.57-23.02-44.27-29.66-.42-.5-24.86-26.41-39.1-66.67-.21-.6-.43-1.21-.63-1.82l-9.34,4.27L30.96,252.8V125.45l25.8-38.39c31.82,5.85,53.22,13.69,63.28,41.84,3.42,9.58,5.53,21.5,6.3,36.5.21,4.23.32,8.72.32,13.46,0,19.95,3.83,38.35,9.37,54.51Z" fill="none">
        <title>right lower</title>
      </path>
    </g>
  </g>
  <g class="app-breast-diagram__diagram" clip-path="url(#clippath)">
    <path data-side="left" vector-effect="non-scaling-stroke" d="M808.48,138.1l-34.3-51.04c-45.7,8.4-69.9,20.9-69.9,91.8s-48.5,122.3-49.1,123c-12.1,14.1-68.7,58.8-146.3,32.4-77.7-26.4-97.1-115.4-97.1-155.5" fill="none" stroke="#212b32" stroke-linecap="round" stroke-width="3">
      <title>left breast outline</title>
    </path>
    <circle data-side="left" vector-effect="non-scaling-stroke" cx="560.31" cy="200" r="22.8" fill="none" stroke="#212b32" stroke-width="3">
      <title>left nipple outline</title>
    </circle>
    <path data-side="right" vector-effect="non-scaling-stroke" d="M-8.5,138.1l34.3-51.04c45.7,8.4,69.9,20.9,69.9,91.8s48.5,122.3,49.1,123c12.1,14.1,68.7,58.8,146.3,32.4,77.7-26.4,97.1-115.4,97.1-155.5" fill="none" stroke="#212b32" stroke-linecap="round" stroke-width="3">
      <title>right breast outline</title>
    </path>
    <circle data-side="right" vector-effect="non-scaling-stroke" cx="239.68" cy="200" r="22.8" fill="none" stroke="#212b32" stroke-width="3">
      <title>right nipple outline</title>
    </circle>
  </g>
</svg>
`

describe('processSvg: test SVG', () => {
  it('produced the expected output', () => {
    const result = processSvg(testSVG, 'test')
    expect(result).toEqual(testSVGProcessed)
  })
})

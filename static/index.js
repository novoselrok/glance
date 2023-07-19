function mean(arr) {
  const sum = arr.reduce((a, b) => a + b, 0);
  return sum / arr.length;
}

function scaleBetween(unscaledNum, minAllowed, maxAllowed, min, max) {
  return (
    ((maxAllowed - minAllowed) * (unscaledNum - min)) / (max - min) + minAllowed
  );
}

function minArray(arr) {
  return Math.min(...arr);
}

function render({ highlightedContent, lineWindows }) {
  const codeTable = document.querySelector("#code");
  codeTable.innerHTML = highlightedContent;

  // Aggregate scores from different windows for a particular line.
  const scoresPerLine = {};
  for (const window of lineWindows) {
    for (let line = window.startLine; line < window.endLine; line++) {
      if (scoresPerLine[line] === undefined) {
        scoresPerLine[line] = [];
      }
      scoresPerLine[line].push(window.score);
    }
  }

  // Average the scores for each line.
  const scorePerLine = {};
  for (const [line, scores] of Object.entries(scoresPerLine)) {
    const score = mean(scores);
    scorePerLine[line] = score;
  }

  const scores = Object.values(scorePerLine);
  const minRange = Math.min(...scores);
  const maxRange = Math.max(...scores);

  // Re-scale all scores between 0 and 0.9 so we can use them as the alpha channel in rgba.
  const scaledScoresPerLine = {};
  for (const [line, score] of Object.entries(scorePerLine)) {
    scaledScoresPerLine[line] = scaleBetween(
      score,
      0.0,
      0.9,
      minRange,
      maxRange
    );
  }

  for (const [key, score] of Object.entries(scaledScoresPerLine)) {
    const line = parseInt(key, 10) + 1;
    const row = document.querySelector(`[data-line="${line}"] + .code`);
    if (!row) {
      continue;
    }
    row.style.backgroundColor = `rgba(255, 180, 255, ${score})`;
  }
}

function initialize() {
  const params = new URLSearchParams(window.location.search);
  const file = params.get("file");

  fetch(`/glance?file=${encodeURIComponent(file)}`)
    .then((response) => response.json())
    .then(render);
}

document.addEventListener("DOMContentLoaded", initialize);

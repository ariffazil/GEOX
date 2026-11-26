import React from 'react';

function scale(values, size) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  return values.map((value) => ((value - min) / span) * size);
}

export function LogTrackViewer({ payload }) {
  const tracks = payload?.tracks || [];
  const height = 360;
  const width = 160;

  return (
    <div className="geox-log-track-viewer">
      <h3>{payload?.title || 'Log Track Viewer'}</h3>
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        {tracks.map((track) => {
          const xs = scale(track.values, width - 20);
          const ys = scale(track.depths, height - 20);
          const points = xs.map((x, index) => `${x + 10},${ys[index] + 10}`).join(' ');
          return (
            <figure key={track.mnemonic} style={{ margin: 0 }}>
              <figcaption>{track.mnemonic}</figcaption>
              <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
                <rect x="0" y="0" width={width} height={height} fill="#0f172a" rx="8" />
                <polyline
                  fill="none"
                  stroke={track.color || '#38bdf8'}
                  strokeWidth="2"
                  points={points}
                />
              </svg>
            </figure>
          );
        })}
      </div>
    </div>
  );
}

export default LogTrackViewer;

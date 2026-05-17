import React from 'react';

function normalize(value, min, max) {
  if (max === min) {
    return 0.5;
  }
  return (value - min) / (max - min);
}

export function VolumeRenderer({ payload }) {
  const values = payload?.values || [];
  const min = payload?.min_value ?? 0;
  const max = payload?.max_value ?? 1;

  return (
    <div className="geox-volume-renderer">
      <h3>{payload?.orientation || 'inline'} slice #{payload?.slice_index ?? 0}</h3>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${payload?.width || 1}, minmax(8px, 1fr))`,
          gap: 1,
          background: '#0f172a',
          padding: 8,
          borderRadius: 8,
        }}
      >
        {values.flat().map((value, index) => {
          const alpha = normalize(value, min, max);
          return (
            <div
              key={index}
              title={`${value}`}
              style={{
                aspectRatio: '1 / 1',
                backgroundColor: `rgba(56, 189, 248, ${alpha.toFixed(3)})`,
              }}
            />
          );
        })}
      </div>
    </div>
  );
}

export default VolumeRenderer;

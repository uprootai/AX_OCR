import React, { useState, useMemo } from 'react';
import services from '../data/services.json';

type SortKey = 'name' | 'port' | 'category';

export default function ServiceTable({ filterCategory }: { filterCategory?: string }) {
  const [sortBy, setSortBy] = useState<SortKey>('port');
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    let result = [...services];
    if (filterCategory) result = result.filter(s => s.category === filterCategory);
    if (search) result = result.filter(s =>
      s.name.toLowerCase().includes(search.toLowerCase()) ||
      s.description.includes(search)
    );
    result.sort((a, b) => {
      if (sortBy === 'port') return a.port - b.port;
      return a[sortBy].localeCompare(b[sortBy]);
    });
    return result;
  }, [filterCategory, search, sortBy]);

  return (
    <div>
      <input
        type="text"
        placeholder="Search services..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        style={{ padding: '8px 12px', marginBottom: '12px', width: '100%', maxWidth: '300px', borderRadius: '6px', border: '1px solid var(--ifm-color-emphasis-300)' }}
      />
      <table className="service-table">
        <thead>
          <tr>
            <th onClick={() => setSortBy('name')} style={{ cursor: 'pointer' }}>
              Service {sortBy === 'name' ? '\u25BC' : ''}
            </th>
            <th onClick={() => setSortBy('port')} style={{ cursor: 'pointer' }}>
              Port {sortBy === 'port' ? '\u25BC' : ''}
            </th>
            <th onClick={() => setSortBy('category')} style={{ cursor: 'pointer' }}>
              Category {sortBy === 'category' ? '\u25BC' : ''}
            </th>
            <th>GPU</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map(s => (
            <tr key={s.id}>
              <td><strong>{s.name}</strong></td>
              <td><code>{s.port}</code></td>
              <td><span className={`badge badge--${s.category}`}>{s.category}</span></td>
              <td><span className={`gpu-badge gpu-badge--${s.gpu ? 'yes' : 'no'}`}>{s.gpu ? 'GPU' : 'CPU'}</span></td>
              <td>{s.description}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p style={{ marginTop: '8px', fontSize: '0.85rem', color: 'var(--ifm-color-emphasis-600)' }}>
        {filtered.length} services
      </p>
    </div>
  );
}

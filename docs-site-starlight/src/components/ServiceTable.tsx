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
        placeholder="서비스 검색..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        style={{ padding: '8px 12px', marginBottom: '12px', width: '100%', maxWidth: '300px', borderRadius: '6px', border: '1px solid var(--sl-color-gray-5)' }}
      />
      <table>
        <thead>
          <tr>
            <th onClick={() => setSortBy('name')} style={{ cursor: 'pointer' }}>
              서비스 {sortBy === 'name' ? '\u25BC' : ''}
            </th>
            <th onClick={() => setSortBy('port')} style={{ cursor: 'pointer' }}>
              포트 {sortBy === 'port' ? '\u25BC' : ''}
            </th>
            <th onClick={() => setSortBy('category')} style={{ cursor: 'pointer' }}>
              카테고리 {sortBy === 'category' ? '\u25BC' : ''}
            </th>
            <th>GPU</th>
            <th>설명</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map(s => (
            <tr key={s.id}>
              <td><strong>{s.name}</strong></td>
              <td><code>{s.port}</code></td>
              <td>{s.category}</td>
              <td>{s.gpu ? 'GPU' : 'CPU'}</td>
              <td>{s.description}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p style={{ marginTop: '8px', fontSize: '0.85rem', color: 'var(--sl-color-gray-3)' }}>
        {filtered.length}개 서비스
      </p>
    </div>
  );
}

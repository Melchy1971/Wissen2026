import { Link, useSearchParams } from 'react-router-dom';

import { StatusBadge } from '../status/StatusBadge.jsx';

export function DocumentTable({ items }) {
  const [searchParams] = useSearchParams();
  const workspaceId = searchParams.get('workspace_id') || '';

  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Titel</th>
          <th>Typ</th>
          <th>Lifecycle</th>
          <th>Status</th>
          <th>Versionen</th>
          <th>Chunks</th>
          <th>Aktualisiert</th>
        </tr>
      </thead>
      <tbody>
        {items.map((item) => (
          <tr key={item.id}>
            <td>
              <Link to={`/documents/${item.id}?workspace_id=${encodeURIComponent(workspaceId)}`}>{item.title}</Link>
            </td>
            <td>{item.mimeType}</td>
            <td><StatusBadge status={item.lifecycleStatus} /></td>
            <td><StatusBadge status={item.importStatus} /></td>
            <td>{item.versionCount}</td>
            <td>{item.chunkCount}</td>
            <td>{item.updatedAtLabel}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
import { Navigate, Route, Routes } from 'react-router-dom';

import { AppShell } from './AppShell.jsx';
import { AdminDiagnosticsPage } from '../pages/AdminDiagnosticsPage.jsx';
import { ChatPage } from '../pages/ChatPage.jsx';
import { DocumentDetailPage } from '../pages/DocumentDetailPage.jsx';
import { DocumentsPage } from '../pages/DocumentsPage.jsx';

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<Navigate replace to="/documents" />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/documents/:id" element={<DocumentDetailPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/chat/:id" element={<ChatPage />} />
        <Route path="/admin/diagnostics" element={<AdminDiagnosticsPage />} />
      </Route>
    </Routes>
  );
}
import { AuthProvider } from '../auth/AuthContext.jsx';
import { AppRoutes } from './routes.jsx';

export function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Toaster } from "@/components/ui/toaster";
import { AuthProvider } from "@/contexts/AuthContext";
import { DashboardPage } from "@/pages/DashboardPage";
import { LoginPage } from "@/pages/LoginPage";
import { SignupPage } from "@/pages/SignupPage";
import {
	Navigate,
	Route,
	BrowserRouter as Router,
	Routes,
} from "react-router-dom";

function App() {
	return (
		<AuthProvider>
			<Router>
				<div className="App">
					<Routes>
						{/* Rotas públicas */}
						<Route path="/login" element={<LoginPage />} />
						<Route path="/signup" element={<SignupPage />} />

						{/* Rotas protegidas */}
						<Route
							path="/dashboard"
							element={
								<ProtectedRoute>
									<DashboardPage />
								</ProtectedRoute>
							}
						/>

						{/* Rota raiz - redireciona para dashboard ou login */}
						<Route path="/" element={<Navigate to="/dashboard" replace />} />

						{/* Rota 404 - redireciona para dashboard */}
						<Route path="*" element={<Navigate to="/dashboard" replace />} />
					</Routes>

					{/* Toast notifications */}
					<Toaster />
				</div>
			</Router>
		</AuthProvider>
	);
}

export default App;

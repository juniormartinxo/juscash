import { useAuth } from "@/contexts/AuthContext";
import React from "react";
import { Navigate, useLocation } from "react-router-dom";

interface ProtectedRouteProps {
	children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
	const { isAuthenticated, loading } = useAuth();
	const location = useLocation();

	// Mostrar loading enquanto verifica autenticação
	if (loading) {
		return (
			<div className="min-h-screen bg-background flex items-center justify-center">
				<div className="text-center">
					<div className="spinner mx-auto mb-4" />
					<p className="text-gray-600">Verificando autenticação...</p>
				</div>
			</div>
		);
	}

	// Redirecionar para login se não autenticado
	if (!isAuthenticated) {
		return <Navigate to="/login" state={{ from: location }} replace />;
	}

	return <>{children}</>;
}

import React from "react"
import ReactDOM from "react-dom/client"
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from "./App.tsx"
import "./index.css"

const queryClient = new QueryClient({
	defaultOptions: {
		queries: {
			staleTime: 0, // Sempre considerar dados stale
			gcTime: 1000 * 60 * 5, // 5 minutos para garbage collection
			retry: 2,
			refetchOnWindowFocus: true,
			refetchOnMount: true,
		},
		mutations: {
			retry: 1,
		},
	},
})

ReactDOM.createRoot(document.getElementById("root")!).render(
	//<React.StrictMode>
	<QueryClientProvider client={queryClient}>
		<App />
	</QueryClientProvider>
	//</React.StrictMode>,
)

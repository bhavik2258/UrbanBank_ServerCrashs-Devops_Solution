import { lazy, Suspense } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes, Navigate, Outlet } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/theme-provider";
import Navbar from "@/components/Navbar";
import { isAuthenticated } from "@/lib/auth";

const Dashboard = lazy(() => import("@/pages/Dashboard"));
const BranchDetail = lazy(() => import("@/pages/BranchDetail"));
const Alerts = lazy(() => import("@/pages/Alerts"));
const Incidents = lazy(() => import("@/pages/Incidents"));
const NotFound = lazy(() => import("@/pages/NotFound"));
const Login = lazy(() => import("@/pages/Login"));

const queryClient = new QueryClient();

const ProtectedRoute = () => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return (
    <div className="min-h-screen bg-slate-50/50 dark:bg-slate-950 flex flex-col">
      <div className="absolute inset-0 bg-grid-slate-200/50 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))] dark:bg-grid-slate-800/50 dark:[mask-image:linear-gradient(0deg,rgba(0,0,0,0.8),rgba(0,0,0,0.4))] pointer-events-none -z-10" />
      <Navbar />
      <main className="flex-1 w-full max-w-[1400px] mx-auto p-4 md:p-6 lg:p-8 animate-in fade-in duration-500 relative z-0">
        <Outlet />
      </main>
    </div>
  );
};

const PublicRoute = () => {
  if (isAuthenticated()) {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
};

const App = () => (
  <ThemeProvider defaultTheme="system" storageKey="opswatch-theme">
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}
        >
          <Suspense fallback={<div className="p-6 text-sm text-muted-foreground">Loading page...</div>}>
            <Routes>
              <Route element={<PublicRoute />}>
                <Route path="/login" element={<Login />} />
              </Route>
              <Route element={<ProtectedRoute />}>
                <Route path="/" element={<Dashboard />} />
                <Route path="/branch/:id" element={<BranchDetail />} />
                <Route path="/alerts" element={<Alerts />} />
                <Route path="/incidents" element={<Incidents />} />
                <Route path="*" element={<NotFound />} />
              </Route>
            </Routes>
          </Suspense>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  </ThemeProvider>
);

export default App;

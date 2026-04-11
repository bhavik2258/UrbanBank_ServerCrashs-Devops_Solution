import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Lock } from "lucide-react";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    // Mock login authentication
    setTimeout(() => {
      setIsLoading(false);
      sessionStorage.setItem("isAuthenticated", "true");
      navigate("/");
    }, 1000);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 relative overflow-hidden dark:bg-slate-950">
      <div className="absolute inset-0 w-full h-full bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
      <div className="relative z-10 w-full max-w-md p-4">
        <div className="flex flex-col items-center mb-8 gap-2">
          <div className="bg-primary p-3 rounded-full text-primary-foreground shadow-lg">
            <Activity className="h-8 w-8" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">UrbanBank OpsWatch</h1>
          <p className="text-muted-foreground text-sm text-center max-w-sm mt-2">
            Centralized IT infrastructure monitoring and incident management portal.
          </p>
        </div>
        <Card className="shadow-2xl border-t-4 border-t-primary">
          <CardHeader className="space-y-1 text-center">
            <CardTitle className="text-2xl">Administrator Login</CardTitle>
            <CardDescription>Enter your staff credentials to access the dashboard</CardDescription>
          </CardHeader>
          <form onSubmit={handleLogin}>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Work Email</Label>
                <Input 
                  id="email" 
                  type="email" 
                  placeholder="admin@urbanbank.com" 
                  required 
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password">Security Token</Label>
                  <a href="#" className="text-xs text-primary hover:underline hover:text-primary/80">
                    Forgot password?
                  </a>
                </div>
                <Input 
                  id="password" 
                  type="password" 
                  placeholder="••••••••" 
                  required 
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </CardContent>
            <CardFooter>
              <Button className="w-full" type="submit" disabled={isLoading}>
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <div className="h-4 w-4 rounded-full border-2 border-background border-t-transparent animate-spin"/>
                    Authenticating...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Lock className="w-4 h-4" /> Secure Sign In
                  </span>
                )}
              </Button>
            </CardFooter>
          </form>
        </Card>
        <div className="text-center mt-8 text-xs text-muted-foreground">
          <p>© 2026 UrbanBank Infrastructure Team.</p>
          <p>Authorized access only. All actions are logged.</p>
        </div>
      </div>
    </div>
  );
}
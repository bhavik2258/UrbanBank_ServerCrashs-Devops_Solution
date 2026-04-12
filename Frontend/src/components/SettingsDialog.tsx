import { useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { Copy, Key, ShieldAlert, BellRing, CheckCircle2 } from "lucide-react";

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsDialog({ open, onOpenChange }: SettingsDialogProps) {
  const [apiKey, setApiKey] = useState("ubk_live_xxxxxxxxxxxxxxxxxxxxxx");

  const handleGenerateKey = () => {
    // Generate a random mock API key string
    const newKey = "ubk_live_" + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
    setApiKey(newKey);
    toast.success("New API Key Generated", {
      description: "Old keys will be invalidated in 24 hours.",
      icon: <CheckCircle2 className="h-4 w-4 text-green-500" />
    });
  };

  const handleCopyKey = () => {
    navigator.clipboard.writeText(apiKey);
    toast.info("API Key copied to clipboard");
  };

  const handleSaveProfile = () => {
    toast.success("Profile Updated", {
      description: "Your changes have been saved successfully.",
      icon: <CheckCircle2 className="h-4 w-4 text-green-500" />
    });
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[550px]">
        <DialogHeader>
          <DialogTitle>Account Settings</DialogTitle>
          <DialogDescription>
            Manage your profile, API access, and alert notification preferences.
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="profile" className="mt-2 w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="profile">Profile</TabsTrigger>
            <TabsTrigger value="notifications">Alerts</TabsTrigger>
            <TabsTrigger value="api">API Keys</TabsTrigger>
          </TabsList>
          
          {/* Profile Tab */}
          <TabsContent value="profile" className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Display Name</Label>
              <Input id="name" defaultValue="System Admin" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email Address (Role)</Label>
              <Input id="email" defaultValue="admin@urbanbank.com" readOnly className="bg-muted" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="avatar">Role</Label>
              <Input id="avatar" defaultValue="IT Operations Level 3" readOnly className="bg-muted" />
            </div>
            <Button onClick={handleSaveProfile} className="w-full mt-4">Save Changes</Button>
          </TabsContent>

          {/* Notifications Tab */}
          <TabsContent value="notifications" className="space-y-4 py-4">
            <div className="flex items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <Label className="text-base flex items-center gap-2">
                  <BellRing className="h-4 w-4 text-primary" /> Critical Alerts
                </Label>
                <DialogDescription>
                  Receive SMS when CPU/RAM exceeds 95%.
                </DialogDescription>
              </div>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <Label className="text-base flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4 text-primary" /> Incident Reports
                </Label>
                <DialogDescription>
                  Daily digest email of all auto-healed incidents.
                </DialogDescription>
              </div>
              <Switch defaultChecked />
            </div>
          </TabsContent>

          {/* API Keys Tab */}
          <TabsContent value="api" className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Production API Key</Label>
              <DialogDescription className="pb-2">
                Use this key to authenticate external CI/CD pipelines (e.g., Jenkins) or Grafana ingestion.
              </DialogDescription>
              <div className="flex items-center gap-2">
                <Input 
                  value={apiKey} 
                  readOnly 
                  className="font-mono text-xs bg-muted"
                  type="password"
                />
                <Button variant="outline" size="icon" onClick={handleCopyKey} title="Copy Key">
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <Button onClick={handleGenerateKey} variant="destructive" className="w-full mt-4 gap-2">
              <Key className="h-4 w-4" /> Revoke & Regenerate Key
            </Button>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
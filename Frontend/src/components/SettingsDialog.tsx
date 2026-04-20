import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { toast } from "sonner";
import { BellRing, CheckCircle2, ShieldCheck } from "lucide-react";

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  userName: string;
  userEmail: string;
  userRole: string;
}

interface NotificationPreferences {
  criticalAlertsEnabled: boolean;
  dailyDigestEnabled: boolean;
}

const getPreferencesStorageKey = (userEmail: string) => `urbanbank.notificationPreferences:${userEmail.toLowerCase()}`;

const readNotificationPreferences = (userEmail: string): NotificationPreferences => {
  if (!userEmail) {
    return { criticalAlertsEnabled: true, dailyDigestEnabled: true };
  }

  const rawPreferences = localStorage.getItem(getPreferencesStorageKey(userEmail));
  if (!rawPreferences) {
    return { criticalAlertsEnabled: true, dailyDigestEnabled: true };
  }

  try {
    const parsedPreferences = JSON.parse(rawPreferences) as Partial<NotificationPreferences>;
    return {
      criticalAlertsEnabled: parsedPreferences.criticalAlertsEnabled ?? true,
      dailyDigestEnabled: parsedPreferences.dailyDigestEnabled ?? true,
    };
  } catch {
    return { criticalAlertsEnabled: true, dailyDigestEnabled: true };
  }
};

const writeNotificationPreferences = (userEmail: string, preferences: NotificationPreferences) => {
  localStorage.setItem(getPreferencesStorageKey(userEmail), JSON.stringify(preferences));
};

export function SettingsDialog({ open, onOpenChange, userName, userEmail, userRole }: SettingsDialogProps) {
  const [criticalAlertsEnabled, setCriticalAlertsEnabled] = useState(true);
  const [dailyDigestEnabled, setDailyDigestEnabled] = useState(true);

  useEffect(() => {
    if (!open) {
      return;
    }

    const savedPreferences = readNotificationPreferences(userEmail);
    setCriticalAlertsEnabled(savedPreferences.criticalAlertsEnabled);
    setDailyDigestEnabled(savedPreferences.dailyDigestEnabled);
  }, [open, userEmail]);

  const handleSavePreferences = () => {
    writeNotificationPreferences(userEmail, {
      criticalAlertsEnabled,
      dailyDigestEnabled,
    });

    toast.success("Preferences updated", {
      description: "Notification preferences were saved successfully.",
      icon: <CheckCircle2 className="h-4 w-4 text-green-500" />
    });
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[550px]">
        <DialogHeader>
          <DialogTitle>My Account</DialogTitle>
          <DialogDescription>
            Review your profile and notification preferences.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="grid gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="account-name">Name</Label>
              <Input id="account-name" value={userName} readOnly className="bg-muted" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="account-email">Email</Label>
              <Input id="account-email" value={userEmail} readOnly className="bg-muted" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="account-role">Role</Label>
              <Input id="account-role" value={userRole} readOnly className="bg-muted" />
            </div>
          </div>

          <div className="rounded-lg border p-4 space-y-3">
            <p className="text-sm font-medium flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-primary" /> Notification Preferences
            </p>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Critical Alert Notifications</p>
                <p className="text-xs text-muted-foreground">Receive immediate alerts for high-severity incidents.</p>
              </div>
              <Switch checked={criticalAlertsEnabled} onCheckedChange={setCriticalAlertsEnabled} />
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Daily Incident Digest</p>
                <p className="text-xs text-muted-foreground">Receive a daily summary of incidents and resolutions.</p>
              </div>
              <Switch checked={dailyDigestEnabled} onCheckedChange={setDailyDigestEnabled} />
            </div>
          </div>

          <div className="rounded-md bg-muted/60 p-3 text-xs text-muted-foreground flex items-center gap-2">
            <BellRing className="h-4 w-4" />
            Access and actions in the system are controlled by your assigned role.
          </div>

          <div className="flex gap-2">
            <Button variant="outline" className="w-full" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button className="w-full" onClick={handleSavePreferences}>
              Save Preferences
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
import { DashboardLayout } from "@/components/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import {
  Settings as SettingsIcon,
  Server,
  Mail,
  Bell,
  Shield,
  Save,
  RefreshCw,
} from "lucide-react";

export default function Settings() {
  return (
    <DashboardLayout>
      <div className="p-6 space-y-6 animate-fade-in">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Settings</h1>
            <p className="text-muted-foreground mt-1">
              Configure system settings and integrations
            </p>
          </div>
          <Button className="gap-2 bg-primary hover:bg-primary/90">
            <Save className="h-4 w-4" />
            Save Changes
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Backend Configuration */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="h-5 w-5 text-primary" />
                Backend Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="backend-url">Face Recognition Backend URL</Label>
                <Input
                  id="backend-url"
                  placeholder="http://localhost:5001"
                  defaultValue="http://localhost:5001"
                  className="bg-secondary border-border"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="stream-endpoint">Video Stream Endpoint</Label>
                <Input
                  id="stream-endpoint"
                  placeholder="/video_feed"
                  defaultValue="/video_feed"
                  className="bg-secondary border-border"
                />
              </div>
              <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                <div className="flex items-center gap-3">
                  <RefreshCw className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm">Auto-reconnect on failure</span>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>

          {/* Email Configuration */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5 text-primary" />
                Email Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="smtp-email">Notification Email</Label>
                <Input
                  id="smtp-email"
                  placeholder="admin@example.com"
                  defaultValue="pilotpranav2007@gmail.com"
                  className="bg-secondary border-border"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="smtp-password">App Password</Label>
                <Input
                  id="smtp-password"
                  type="password"
                  placeholder="••••••••••••••••"
                  defaultValue="wuvqfqcnvjfywdmi"
                  className="bg-secondary border-border"
                />
                <p className="text-xs text-muted-foreground">
                  Use Gmail App Password for secure SMTP authentication
                </p>
              </div>
              <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                <p className="text-xs text-amber-400">
                  <strong>Security:</strong> In production, store credentials in environment variables
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Notification Settings */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5 text-primary" />
                Notification Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                <div>
                  <p className="font-medium text-foreground">Auto-send absentee emails</p>
                  <p className="text-sm text-muted-foreground">Send email after each class ends</p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                <div>
                  <p className="font-medium text-foreground">Low attendance alerts</p>
                  <p className="text-sm text-muted-foreground">Alert when student falls below 75%</p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                <div>
                  <p className="font-medium text-foreground">Bunking detection alerts</p>
                  <p className="text-sm text-muted-foreground">Real-time notification on detection</p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                <div>
                  <p className="font-medium text-foreground">Daily summary report</p>
                  <p className="text-sm text-muted-foreground">Send daily attendance summary</p>
                </div>
                <Switch />
              </div>
            </CardContent>
          </Card>

          {/* Security Settings */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-primary" />
                Security & Access
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                <div>
                  <p className="font-medium text-foreground">Require authentication</p>
                  <p className="text-sm text-muted-foreground">Secure access to dashboard</p>
                </div>
                <Badge className="status-active">Enabled</Badge>
              </div>
              <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                <div>
                  <p className="font-medium text-foreground">Session timeout</p>
                  <p className="text-sm text-muted-foreground">Auto-logout after inactivity</p>
                </div>
                <Badge variant="secondary">30 mins</Badge>
              </div>
              <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                <div>
                  <p className="font-medium text-foreground">API rate limiting</p>
                  <p className="text-sm text-muted-foreground">Prevent abuse of endpoints</p>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}

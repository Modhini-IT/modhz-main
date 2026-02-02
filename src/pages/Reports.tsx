import { DashboardLayout } from "@/components/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  FileText,
  Download,
  Calendar,
  Mail,
  AlertTriangle,
  CheckCircle,
} from "lucide-react";

const reports = [
  {
    id: 1,
    title: "Weekly Attendance Report",
    date: "2026-01-27",
    type: "attendance",
    status: "ready",
    emails: 3,
  },
  {
    id: 2,
    title: "Absentee Notification - IT22201",
    date: "2026-01-27",
    type: "absentee",
    status: "sent",
    emails: 5,
  },
  {
    id: 3,
    title: "Low Attendance Alert",
    date: "2026-01-26",
    type: "alert",
    status: "sent",
    emails: 3,
  },
  {
    id: 4,
    title: "Daily Summary - Monday",
    date: "2026-01-27",
    type: "summary",
    status: "ready",
    emails: 0,
  },
  {
    id: 5,
    title: "Absentee Notification - MA22251",
    date: "2026-01-26",
    type: "absentee",
    status: "sent",
    emails: 8,
  },
];

const absenteeHistory = [
  {
    date: "2026-01-27",
    subject: "IT22201",
    time: "08:30 - 09:20",
    absentees: ["Kumar S", "Arun K", "Deepa R"],
    emailSent: true,
  },
  {
    date: "2026-01-27",
    subject: "MA22251",
    time: "09:20 - 10:10",
    absentees: ["Arun K", "Priya N"],
    emailSent: true,
  },
  {
    date: "2026-01-26",
    subject: "HS22252",
    time: "08:30 - 09:20",
    absentees: ["Kumar S", "Arun K", "Deepa R", "Vijay M"],
    emailSent: true,
  },
];

export default function Reports() {
  return (
    <DashboardLayout>
      <div className="p-6 space-y-6 animate-fade-in">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">Reports & Notifications</h1>
            <p className="text-muted-foreground mt-1">
              View attendance reports and email notification history
            </p>
          </div>
          <Button className="gap-2 bg-primary hover:bg-primary/90">
            <FileText className="h-4 w-4" />
            Generate Report
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Generated Reports */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                Generated Reports
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {reports.map((report) => (
                  <div
                    key={report.id}
                    className="flex items-center justify-between p-4 rounded-lg bg-secondary/30 hover:bg-secondary/50 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${
                        report.type === "alert"
                          ? "bg-amber-500/10"
                          : report.type === "absentee"
                          ? "bg-destructive/10"
                          : "bg-primary/10"
                      }`}>
                        {report.type === "alert" ? (
                          <AlertTriangle className="h-5 w-5 text-amber-400" />
                        ) : report.type === "absentee" ? (
                          <Mail className="h-5 w-5 text-destructive" />
                        ) : (
                          <FileText className="h-5 w-5 text-primary" />
                        )}
                      </div>
                      <div>
                        <p className="font-medium text-foreground">{report.title}</p>
                        <p className="text-sm text-muted-foreground flex items-center gap-2">
                          <Calendar className="h-3 w-3" />
                          {new Date(report.date).toLocaleDateString()}
                          {report.emails > 0 && (
                            <span className="flex items-center gap-1">
                              <Mail className="h-3 w-3" />
                              {report.emails} sent
                            </span>
                          )}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        className={
                          report.status === "sent"
                            ? "status-active"
                            : "bg-primary/20 text-primary border border-primary/30"
                        }
                      >
                        {report.status === "sent" ? (
                          <span className="flex items-center gap-1">
                            <CheckCircle className="h-3 w-3" />
                            Sent
                          </span>
                        ) : (
                          "Ready"
                        )}
                      </Badge>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <Download className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Absentee Email History */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5 text-primary" />
                Absentee Email History
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {absenteeHistory.map((record, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-lg bg-secondary/30 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-mono text-primary font-medium">{record.subject}</p>
                        <p className="text-sm text-muted-foreground">
                          {new Date(record.date).toLocaleDateString()} • {record.time}
                        </p>
                      </div>
                      <Badge className="status-active">
                        <Mail className="h-3 w-3 mr-1" />
                        Email Sent
                      </Badge>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground mb-2">Absentees ({record.absentees.length}):</p>
                      <div className="flex flex-wrap gap-2">
                        {record.absentees.map((name) => (
                          <Badge key={name} variant="secondary" className="text-xs">
                            {name}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-4 p-3 bg-secondary/20 rounded-lg">
                <strong>Note:</strong> Emails are automatically sent to pilotpranav2007@gmail.com 
                after each class ends with the list of absent students.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Email Configuration Notice */}
        <Card className="bg-card border-border border-l-4 border-l-primary">
          <CardContent className="py-4">
            <div className="flex items-start gap-4">
              <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <Mail className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold text-foreground">Email Automation Active</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Absentee notifications are automatically sent after each class period ends. 
                  The system uses the configured SMTP credentials to send emails securely.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}

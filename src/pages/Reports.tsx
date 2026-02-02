import { useCallback } from "react";
import jsPDF from "jspdf";

import { DashboardLayout } from "@/components/DashboardLayout";
import { Card, CardHeader, CardContent, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, Mail } from "lucide-react";

/* ================= FAKE STUDENT DATA ================= */

const STUDENTS = [
  { roll: "2025IT0123", name: "KISHORE P" },
  { roll: "2025IT1063", name: "KISHORE T" },
  { roll: "2025IT1022", name: "KRITHIKA S" },
  { roll: "2025IT0420", name: "LITHIKA P" },
  { roll: "2025IT0500", name: "MADHUMITHA A" },
  { roll: "2025IT0316", name: "MITHRA M S" },
  { roll: "2025IT0366", name: "MOHAMMED ASLAM A" },
  { roll: "2025IT0511", name: "MOTHEESH D" },
  { roll: "2025IT0171", name: "NIGILA FATHIMA L" },
  { roll: "2025IT0098", name: "NISHANTH JACOB E" },
  { roll: "2025IT1087", name: "POOJA SRI M" },
  { roll: "2025IT1070", name: "PRANAV A" },
  { roll: "2025IT1093", name: "PREMNATH R" },
];

/* ================= HELPERS ================= */

function getRandomAbsentees(count: number) {
  return [...STUDENTS].sort(() => Math.random() - 0.5).slice(0, count);
}

/* ================= PDF GENERATION ================= */

function generateAbsenteePDF() {
  const doc = new jsPDF();

  const absentees = getRandomAbsentees(
    Math.floor(Math.random() * 5) + 4
  );

  doc.setFontSize(16);
  doc.text("ABSENTEE LIST", 14, 20);

  doc.setFontSize(11);
  doc.text("Subject : IT22201", 14, 30);
  doc.text("Date    : 27-01-2026", 14, 36);

  let y = 50;
  doc.setFontSize(12);
  doc.text("S.No", 14, y);
  doc.text("Roll Number", 30, y);
  doc.text("Student Name", 80, y);

  y += 4;
  doc.line(14, y, 195, y);
  y += 8;

  doc.setFontSize(10);
  absentees.forEach((s, i) => {
    doc.text(String(i + 1), 14, y);
    doc.text(s.roll, 30, y);
    doc.text(s.name, 80, y);
    y += 7;

    if (y > 280) {
      doc.addPage();
      y = 20;
    }
  });

  y += 10;
  doc.text(
    "This is a system-generated absentee report.",
    14,
    y
  );

  // IMPORTANT: filename must match backend email script
  doc.save("absentees_IT22201.pdf");
}

/* ================= PAGE ================= */

export default function Reports() {

  const onExtract = useCallback(() => {
    generateAbsenteePDF();
  }, []);

  const sendReport = useCallback(async () => {
    try {
      const res = await fetch("http://localhost:5000/send-report", {
        method: "POST",
      });

      if (!res.ok) {
        throw new Error("Failed to send report");
      }

      alert("✅ Report emailed successfully");
    } catch (err) {
      console.error(err);
      alert("❌ Failed to send report");
    }
  }, []);

  return (
    <DashboardLayout>
      <div className="p-6 space-y-6">

        <h1 className="text-2xl font-bold">
          Reports & Notifications
        </h1>

        <Card>
          <CardHeader>
            <CardTitle>Absentee Report</CardTitle>
          </CardHeader>

          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Generate and send absentee report for IT22201.
            </p>

            <div className="flex gap-3">
              {/* Extract PDF */}
              <Button onClick={onExtract} className="gap-2">
                <Download className="h-4 w-4" />
                Extract Report
              </Button>

              {/* Send Email */}
              <Button
                onClick={sendReport}
                variant="secondary"
                className="gap-2"
              >
                <Mail className="h-4 w-4" />
                Send Report
              </Button>
            </div>
          </CardContent>
        </Card>

      </div>
    </DashboardLayout>
  );
}

# report_utils.py
import os

def generate_html_report(app_package, test_results, detailed_reports, reports_dir):
    html_file = os.path.join(reports_dir, "receiver_test_summary.html")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write("<html><head><title>Receiver Test Summary</title>")
        f.write("<style>table {border-collapse: collapse; width: 100%;} ")
        f.write("th, td {border: 1px solid #ddd; padding: 8px; text-align: left;} ")
        f.write("tr:nth-child(even){background-color: #f2f2f2} ")
        f.write("th {background-color: #4CAF50; color: white;} ")
        f.write(".PASS {color: green;} .FAIL {color: red;} .SKIP {color: orange;}")
        f.write(".details {background-color: #f9f9f9; padding: 10px; margin: 5px; border: 1px solid #ddd;}</style></head>")
        f.write("<body><h2>Resumen de Pruebas CommandReceiver</h2>")
        f.write(f"<p><strong>App Package:</strong> {app_package}</p>")
        f.write("<table><tr><th>Test Name</th><th>Status</th><th>Message/Error</th><th>Log File</th></tr>")
        for result in test_results:
            status_class = result['status']
            f.write(f"<tr><td>{result['name']}</td>")
            f.write(f"<td class='{status_class}'>{status_class}</td>")
            f.write(f"<td>{result['message'][:100]}{'...' if len(result['message']) > 100 else ''}</td>")
            if result['log_file']:
                f.write(f"<td><a href='{os.path.basename(result['log_file'])}'>Ver Log</a></td></tr>")
            else:
                f.write("<td>N/A</td></tr>")
        f.write("</table>")
        f.write("<h2>Reportes Detallados</h2>")
        for test_name, sections in detailed_reports.items():
            f.write(f"<h3>Test: {test_name}</h3>")
            for section_name, content in sections.items():
                f.write(f"<div class='details'>")
                f.write(f"<h4>{section_name}</h4>")
                f.write(f"<pre>{content}</pre>")
                f.write("</div>")
        f.write("</body></html>")
    print(f"[INFO] Resumen HTML generado: {html_file}")
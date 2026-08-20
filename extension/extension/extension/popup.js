document.getElementById('btnPrint').addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: triggerCleanPrint
  });
});

function triggerCleanPrint() {
  const receiptElement = document.getElementById('printable-receipt-card');
  if (!receiptElement) {
    alert("⚠️ Open the 'Print Slip' page first to load the receipt!");
    return;
  }

  const printWindow = window.open('', '_blank', 'width=650,height=900');
  const receiptHTML = `
    <!DOCTYPE html>
    <html>
      <head>
        <title>Receipt_Print</title>
        <style>
          @page { size: A5 portrait; margin: 6mm; }
          body { font-family: 'Courier New', monospace; background: #FFF; color: #000; margin: 0; padding: 10px; font-size: 12.5px; }
          #printable-receipt-card { width: 100%; max-width: 140mm; margin: 0 auto; border: 1px solid #000; padding: 14px; box-sizing: border-box; }
          table { width: 100%; border-collapse: collapse; }
          td, th { padding: 3px 2px; }
          hr { border: none; border-top: 1px dashed #000; margin: 8px 0; }
        </style>
      </head>
      <body>
        ${receiptElement.outerHTML}
      </body>
    </html>
  `;

  printWindow.document.open();
  printWindow.document.write(receiptHTML);
  printWindow.document.close();
  printWindow.focus();
  setTimeout(() => {
    printWindow.print();
    printWindow.close();
  }, 250);
}

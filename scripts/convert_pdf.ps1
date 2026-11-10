$w=New-Object -ComObject Word.Application
$w.Visible=$false
$w.DisplayAlerts=0
try{
 $d=$w.Documents.Open("D:\dev\projects\taobao-analysis\report\preview.docx",$false,$true)
 $d.SaveAs([ref]"D:\dev\projects\taobao-analysis\report\preview.pdf",[ref]17)
 $d.Close($false)
 Write-Output "PDF_OK"
}catch{ Write-Output ("PDF_ERR "+$_.Exception.Message) }
finally{ $w.Quit() }

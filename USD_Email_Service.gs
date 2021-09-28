//this is a function that fires when the webapp receives a GET request
function doGet(e) {
  return HtmlService.createHtmlOutput("request received");
}

//this is a function that fires when the webapp receives a POST request
function doPost(e) {
  var sentData = JSON.parse(e.postData.contents);
  for (var entry in sentData) {
    var type = sentData[entry].type;
    var date = sentData[entry].date;
    var property = sentData[entry].property;
    var amount = sentData[entry].amount;
    var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = spreadsheet.getSheetByName("Transactions");
    var lastRow = Math.max(sheet.getLastRow(),1);
    sheet.insertRowAfter(lastRow);
    sheet.getRange(lastRow + 1, 1).setValue(date);
    sheet.getRange(lastRow + 1, 2).setValue(property);
    if (type == "Sell"){
      sheet.getRange(lastRow + 1, 4).setValue(amount);
    }
    else{
      sheet.getRange(lastRow + 1, 3).setValue(amount);
    }
    SpreadsheetApp.flush();
  }
  return HtmlService.createHtmlOutput("Post request received");
}
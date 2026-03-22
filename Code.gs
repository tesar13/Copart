function doGet() {
  return HtmlService.createHtmlOutputFromFile('index');
}

// kurs EUR z NBP
function getEuroRate() {
  const url = "https://api.nbp.pl/api/exchangerates/rates/A/EUR/?format=json";
  const response = UrlFetchApp.fetch(url);
  const data = JSON.parse(response.getContentText());
  return data.rates[0].mid;
}

// prowizja aukcyjna
function getAuctionFee(price) {
  if (price > 15000) return price * 0.05;

  const table = [
    [100,200,25],[200,300,50],[300,350,75],[350,400,100],
    [400,450,110],[450,500,120],[500,550,130],[550,600,140],
    [600,700,150],[700,800,160],[800,900,170],[900,1000,180],
    [1000,1199,200],[1200,1300,210],[1300,1400,220],[1400,1500,230],
    [1500,1600,240],[1600,1700,250],[1700,1800,260],[1800,2000,270],
    [2000,2400,280],[2400,2500,290],[2500,3000,310],[3000,3500,350],
    [3500,4000,400],[4000,4500,440],[4500,5000,480],[5000,5500,500],
    [5500,6000,540],[6000,6500,580],[6500,7000,600],[7000,7500,620],
    [7500,8000,640],[8000,8500,650],[8500,9000,660],[9000,10000,670],
    [10000,10500,680],[10500,11000,690],[11000,11500,700],
    [11500,12000,720],[12000,12500,740],[12500,15000,760]
  ];

  for (let i = 0; i < table.length; i++) {
    const [min, max, fee] = table[i];
    if (price >= min && price < max) return fee;
  }

  return 0;
}

function calculate(price, hybrid, engine, vat) {
  const eurRate = getEuroRate();

  let CenaPLN = price * eurRate;

  // AKCYZA
  if (hybrid === "Nie") {
    CenaPLN += (engine === "small" ? 0.031 : 0.186) * CenaPLN;
  }

  if (hybrid === "PHEV") {
    if (engine === "medium") CenaPLN += 0.093 * CenaPLN;
    if (engine === "large") CenaPLN += 0.186 * CenaPLN;
  }

  if (hybrid === "HEV") {
    if (engine === "small") CenaPLN += 0.0155 * CenaPLN;
    if (engine === "medium") CenaPLN += 0.093 * CenaPLN;
    if (engine === "large") CenaPLN += 0.186 * CenaPLN;
  }

  // VAT
  if (vat === "Tak") {
    CenaPLN += 0.23 * CenaPLN;
  }

  // PROWIZJA
  const feeEUR = getAuctionFee(price);
  const feePLN = feeEUR * eurRate;

  CenaPLN += feePLN;

  // STAŁA OPŁATA
CenaPLN += 2000;

  return Math.round(CenaPLN).toLocaleString('pl-PL') + " zł";
}

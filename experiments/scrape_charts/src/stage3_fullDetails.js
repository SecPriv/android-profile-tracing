const fs = require('fs')
const gplay = require('google-play-scraper').memoized()
const session = require('./session.json')

const lang = session.lang
const country = session.country
const fullDetailsPath = session.fullDetailsPath
const downloadDelay = session.downloadDelay
const simultaneousDownloads = session.simultaneousDownloads

const appIds = require(session.chartsJsonPath)

console.log("Downloading app details")

/*
async function handleRequest(i) {
    const appId = appIds[i];
    if (appId) {
        gplay.app({ appId: appId, lang: lang, country: country }).then(result => fs.writeFile(fullDetailsPath + result.appId + ".json", JSON.stringify(result), (err) => { if (err) { console.log(err) } }), err => console.log(err))
        setTimeout(() => { handleRequest(i + simultaneousDownloads) }, downloadDelay);
    }
}*/

async function handleRequest(i) {
    const appId = appIds[i];
    console.log(i, appId)
    if (appId) {
        const result = await gplay.app({ appId: appId, lang: lang, country: country }).catch(e => { console.log(e); return false })
        if (result) {
            fs.writeFile(fullDetailsPath + result.appId + ".json", JSON.stringify(result), (err) => { if (err) { console.log(err) } })
        }
        setTimeout(() => { handleRequest(i + simultaneousDownloads) }, downloadDelay);
    }
}


for (let i = 0; i < simultaneousDownloads; i++) {
    setTimeout(function () { handleRequest(i) }, i * downloadDelay / simultaneousDownloads);
}


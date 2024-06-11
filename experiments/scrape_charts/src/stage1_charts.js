const fs = require('fs')
const gplay = require('google-play-scraper').memoized()
const session = require("./session.json")

const listNum = 1000 //apparently tops out at 660?
const lang = session.lang
const country = session.country
const chartsPath = session.chartsPath

const categories = Object.values(gplay.category);
const collections = Object.values(gplay.collection);
const ages = Object.values(gplay.age);

const args_list = []
const chart_promises = []

console.log("Downloading charts")

function ifErr(err) {
    if (err) {
        console.log(err)
    }
}

async function handleTopApps(list) {
    let counter = 0
    for (resolvedPromise of list) {
        args = args_list[counter]
        argsString = args.join("-")
        if (resolvedPromise.status === "fulfilled") {
            path = chartsPath + argsString + ".json"
            fs.writeFile(path, JSON.stringify(resolvedPromise.value), ifErr)
        } else {
            console.log("ERROR: " + argsString + " " + JSON.stringify(resolvedPromise.value))
        }
        counter++
    }
}

// DOC creates the list of charts to get
for (const category of categories) {
    for (const collection of collections) {
        if (category.startsWith("FAMILY")) {
            for (const age of ages) {
                args_list.push([category, collection, age])
                chart_promises.push(gplay.list({ category: category, collection: collection, age: age, num: listNum, lang: lang, country: country }))
            }
        } else {
            args_list.push([category, collection])
            chart_promises.push(gplay.list({ category: category, collection: collection, num: listNum, lang: lang, country: country }))
        }
    }
}

Promise.allSettled(chart_promises).then(handleTopApps)

import { json, urlencoded, static as staticfile } from "express";
import test from "./test.mjs";

import path from 'path';
import { fileURLToPath } from 'url';
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

console.log('Setting up routes')
var public_path = __dirname+'/../public'

export default function(app) {
  app.use(json({limit:'50mb'}));
  app.use(urlencoded({limit:'50mb', extended: true }));
  
  app.use("/test", test);
  app.use("/", (req, res)=>res.send('Hello, world!'));

  app.use(staticfile(public_path)); //leave this as last use statement!

  
};
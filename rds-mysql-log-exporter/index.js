const zlib = require('zlib');
const fs = require('fs');
const rdsid = '<your rdsid>';
const bucket = '<your bucket>';
const AWS = require('aws-sdk');
AWS.config.update({region: 'cn-northwest-1'});

function listLog(context) {

        let params = {
                DBInstanceIdentifier: rdsid,
                // filter for non 0-byte file rotated in 1 hour
                FileLastWritten: Date.now() - 3600000,
                FileSize: '1',
                FilenameContains: 'log.'
        };

        let request = new AWS.RDS().describeDBLogFiles(params);
        request.on('success', (response) => {
                console.log(response.data);
                getRdsLog(context, response.data.DescribeDBLogFiles, '0');
        }).on('error', (err) => {
                context.fail(err);
        }).send();
}

function getRdsLog(context, logArray, marker) {

        if (!logArray[0]) return;
        let logObj = logArray[0];
        let s3name = logObj.LogFileName.slice(0,5) + '-' + rdsid + '-' + logObj.LastWritten + '.log.gz';

        let params = {
                DBInstanceIdentifier: rdsid,
                LogFileName: logObj.LogFileName,
                Marker: marker
        };

        let request = new AWS.RDS().downloadDBLogFilePortion(params);
        request.on('success', (response) => {
                console.log(s3name + ' ' + response.data.Marker);
                try {
                        fs.appendFileSync('/tmp/' + s3name, zlib.gzipSync(response.data.LogFileData));
                }
                catch (err) {
                        context.fail(err);
                };
                if (response.data.AdditionalDataPending) {
                        getRdsLog(context, logArray, response.data.Marker);
                }
                else {
                        console.log(s3name + ' downloaded');
                        logArray.shift();
                        putLog(context, s3name, logArray);
                }
        }).on('error', (err) => {
                context.fail(err);
        }).send();
}

function putLog(context, s3name, logArray) {

        let params = {
                Body: fs.readFileSync('/tmp/' + s3name),
                Bucket: bucket,
                ContentType: 'text/plain',
                ContentEncoding: 'gzip',
                ServerSideEncryption: 'AES256',
                Key: 'RDS/' + rdsid + '/' + s3name.slice(0, 5) + '/' + new Date().toISOString().slice(0,10) + '/' + s3name
        };

        let request = new AWS.S3().putObject(params);
        request.on('success', () => {
                console.log(s3name + ' uploaded to S3');
                fs.unlinkSync('/tmp/' + s3name);
                getRdsLog(context, logArray, '0');
        }).on('error', (err) => {
                context.fail(err);
        }).send();
}

exports.handler = function(event, context) {

        listLog(context);
};


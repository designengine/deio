'use strict';
console.log('Loading function');

const AWS = require('aws-sdk');
const sns = new AWS.SNS();


/**
 * Provide an event that contains the following keys:
 *
 *   - operation: one of the operations in the switch statement below
 *   - tableName: required for operations that interact with DynamoDB
 *   - payload: a parameter to pass to the operation being performed
 */
exports.handler = (event, context, callback) => {
    console.log('Received event:', JSON.stringify(event, null, 2));

    if (event.challenge) {
        callback(event.challenge);
    }

    // SQS adding message.
    // var params = {
    //     MessageBody: JSON.stringify(event),
    //     QueueUrl: 'https://sqs.us-east-1.amazonaws.com/594618010456/DEioBotSlackMessage'
    // }

    // sqs.sendMessage(params, function(error, data) {
    //     if (error) {
    //         console.log(error, error.stack)
    //     }
    //     else {
    //         console.log(data)
    //         callback()
    //     }
    // })



    if (event.event.subtype == 'bot_message') {
        callback({'ok':true});
        return;
    }
    else if (event.event.subtype == 'file_comment' || event.event.type == 'message') {
        var params = {
            Message: JSON.stringify(event, null, 2),
            Subject: "Slack Bot Event API",
            TopicArn: "arn:aws:sns:us-east-1:594618010456:DEioBotSlackEvent"
        };

        sns.publish(params, function(error, data){
            if (error) {
                console.log("SNS Publish Error", error);
            }
            else {
                console.log("SNS Publish Data", data);
            }
        });

    } else {
        console.log('Event not accepted at the time.');
    }


};

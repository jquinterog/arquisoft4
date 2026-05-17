exports.handler = async function (context, event, callback) {
  const twiml = new Twilio.twiml.VoiceResponse();
  const got = require('got');

  // Verificar si ya tenemos una respuesta del usuario
  if (event.SpeechResult) {
    console.log('Respuesta recibida:', event.SpeechResult);
    console.log('Confianza:', event.Confidence);

    // Preparar el objeto para enviar
    const requestBody = {
      name: event.SpeechResult,
      description: event.SpeechResult,
      type: "NEXT_BEST_OFFER",
      channel: "CALL_CENTER",
      priority: 1,
      start_date: "2026-05-20T10:00:00Z",
      end_date: "2026-06-25T10:00:00Z",
      action_message: event.SpeechResult,
    };

    try {
      // Hacer la llamada POST
      const endpoint = `https://${context.BACKEND_DOMAIN}/promociones`;
      const response = await got.post(endpoint, {
        json: requestBody,
        responseType: 'json',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      console.log('Respuesta del endpoint:', response.body);

      // Confirmar al usuario
      twiml.say({language: 'es-US'}, `Entendí: ${event.SpeechResult}. Gracias por tu respuesta.`);
    } catch (error) {
      console.error('Error llamando al endpoint:', error.message);
      twiml.say({language: 'es-US'}, 'Hubo un error procesando tu respuesta. Por favor intenta de nuevo.');
    }
    twiml.hangup();
  } else {
    // Primera llamada - hacer la pregunta
    const gather = twiml.gather({
      input: 'speech',
      language: 'es-US',
      speechModel: 'phone_call',
      speechTimeout: 5,
      action: '' // Vacío para que vuelva a esta misma función
    });
    gather.say({language: 'es-US'}, '¿Qué promoción desea crear?');

    // Si el usuario no responde, repetir
    twiml.say({language: 'es-US'}, 'No escuché ninguna respuesta.');
    twiml.hangup();
  }

  console.log('TwiML generado:', twiml.toString());
  callback(null, twiml);
};

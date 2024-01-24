import time
from iqoptionapi.stable_api import IQ_Option
from state import user_choices

def connect_iq_option(email, password, account_type):
    API = IQ_Option(email, password)
    check, reason = API.connect()
    if check:
        return API, account_type, True
    else:
        if reason == '{"code":"invalid_credentials","message":"You entered the wrong credentials. Please ensure that your login/password is correct."}':
            print('Invalid email or password.')
        else:
            print('\nConnection timeout...')
            print(f'{reason}')
        return None, None, False

def purchase_with_gale(API, marker, input_value, direction, expiration, type, gale_quantity, gale_multiplier, bot, chat_id):
    for attempt in range(gale_quantity):
        stop_command = user_choices.get(chat_id, {}).get("stop_command_triggered")
        if stop_command:
            break
        if type == 'digital' or type == 'binary':
            check, id = API.buy_digital_spot_v2(marker, input_value, direction, expiration)
        else:
            check, id = API.buy(input_value, marker, direction, expiration)

        if check:
            while True:
                time.sleep(0.1)
                status, result = API.check_win_digital_v2(id) if type == 'digital' or 'binary' else API.check_win_v4(id)

                if status:
                    if result > 0:
                        return {"result": f"✅ Operation With Gain ✅\nValue: ${round(result, 2)}.", "amount": round(result, 2)}
                    elif result == 0:
                        return {"result": f"🔷 Operation With Draw 🔷\nValue: ${round(result, 2)}.", "amount": round(result, 2)}
                    else:
                        loss_amount = abs(result)
                        loss_info = f"❌ Operation With Loss ❌\nValue: -${round(loss_amount, 2)}\nRemaining Attempts: {gale_quantity - attempt - 1}\nMultiplier: {gale_multiplier}"
                        bot.send_message(chat_id, loss_info)
                        break

        else:
            return {"result": "Error opening order.\n\nThe position value is greater than allowed in the configuration.\n\nUse the /reset_purchase command and start the purchase process again with valid data."}

        input_value *= gale_multiplier
    if stop_command:
        return {"result": "Gale's strategy was paused due to the /stop command."}
    else:
        return {"result": "Maximum amount of Gale reached."}

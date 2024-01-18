import time
from iqoptionapi.stable_api import IQ_Option

def connect_iq_option(email, password, account_type):
    API = IQ_Option(email, password)
    check, reason = API.connect()

    if check:
        print('\nConectado com sucesso!')
        return API, account_type, True
    else:
        if reason == '{"code":"invalid_credentials","message":"You entered the wrong credentials. Please ensure that your login/password is correct."}':
            print('E-mail ou senha inválidos.')
        else:
            print('\nTempo limite de conexão...')
            print(f'{reason}')
        return None, None, False

def purchase_with_gale(API, marker, input_value, direction, expiration, type, gale_quantity, gale_multiplier):
    print("Chegou na função 'purchase_with_gale'")
    for attempt in range(gale_quantity):
        if type == 'digital':
            print(f'Marker: {marker}.\nTimeFrame: {expiration}.\nInput Value: {input_value}.')
            check, id = API.buy_digital_spot_v2(marker, input_value, direction, expiration)
        else:
            check, id = API.buy(input_value, marker, direction, expiration)

        if check:
            print(f'Ordem executada {id}.')

            while True:
                time.sleep(0.1)
                status, result = API.check_win_digital_v2(id) if type == 'digital' else API.check_win_v4(id)

                if status:
                    if result > 0:
                        print(f'Resultado: WIN {round(result, 2)}.')
                        return {"result": f"WIN ${round(result, 2)}.", "amount": round(result, 2)}
                    elif result == 0:
                        print(f'Resultado: DRAW {round(result, 2)}.')
                        return {"result": f"DRAW ${round(result, 2)}.", "amount": round(result, 2)}
                    else:
                        print(f'Resultado: LOSS {round(result, 2)}.')
                        return {"result": f"LOSS ${round(result, 2)}."}
                        break

        else:
            print(f'Erro ao abrir a ordem, {id}.')

        input_value *= gale_multiplier

    return {"result": "Quantidade máxima de Gale atingida"}

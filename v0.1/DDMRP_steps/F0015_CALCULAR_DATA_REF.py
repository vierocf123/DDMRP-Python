import datetime as dt

def def_calcular_data(data_ref, datas_bloqueadas, dias_corridos,tipo=True):
        
        """Calcula a data_ref mais dias corridos, desconsiderando as datas presentes
        em datas_bloqueadas, TIPO = True calculo para o futuro,
        TIPO = False calculo para o passado.
        
        Retorna data_ref + dias corridos"""
        
        day = 1
        if tipo == False: day=-1

        dias_adicionados = 0
        data_resp = data_ref

        while dias_adicionados < dias_corridos:
             data_resp += dt.timedelta(days=day)
             if data_resp not in datas_bloqueadas:
                  dias_adicionados +=1

        return(data_resp)
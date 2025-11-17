from database.impianto_DAO import ImpiantoDAO
from database.consumo_DAO import ConsumoDAO

'''
    MODELLO:
    - Rappresenta la struttura dati
    - Si occupa di gestire lo stato dell'applicazione
    - Interagisce con il database
'''


class Model:
    def __init__(self):
        self._impianti = None
        self.load_impianti()

        self.__sequenza_ottima = []
        self.__costo_ottimo = -1

    def load_impianti(self):
        """ Carica tutti gli impianti e li setta nella variabile self._impianti """
        self._impianti = ImpiantoDAO.get_impianti()

    def get_consumo_medio(self, mese: int):
        """
        Calcola, per ogni impianto, il consumo medio giornaliero per il mese selezionato.
        :param mese: Mese selezionato (un intero da 1 a 12)
        :return: lista di tuple --> (nome dell'impianto, media), es. (Impianto A, 123)
        """
        risultato = []
        for impianto in self._impianti:
            if impianto.lista_consumi is None:
                impianto.lista_consumi = ConsumoDAO.get_consumi(impianto.id)

            consumi_impianto = impianto.get_consumi()
            consumi_mese = []
            if consumi_impianto:
                for consumo in consumi_impianto:
                    if consumo.data.month == mese:
                        consumi_mese.append(consumo.kwh)

            if len(consumi_mese) > 0:
                media_mese = sum(consumi_mese) / len(consumi_mese)
                risultato.append((impianto.nome, round(media_mese, 2)))
            else:
                risultato.append((impianto.nome, 0))

        return risultato

    def get_sequenza_ottima(self, mese:int):
        """
        Calcola la sequenza ottimale di interventi nei primi 7 giorni
        :return: sequenza di nomi impianto ottimale
        :return: costo ottimale (cioè quello minimizzato dalla sequenza scelta)
        """
        self.__sequenza_ottima = []
        self.__costo_ottimo = -1
        consumi_settimana = self.__get_consumi_prima_settimana_mese(mese)

        self.__ricorsione([], 1, None, 0, consumi_settimana)

        # Traduci gli ID in nomi
        id_to_nome = {impianto.id: impianto.nome for impianto in self._impianti}
        sequenza_nomi = [f"Giorno {giorno}: {id_to_nome[i]}" for giorno, i in enumerate(self.__sequenza_ottima, start=1)]
        return sequenza_nomi, self.__costo_ottimo

    def __ricorsione(self, sequenza_parziale, giorno, ultimo_impianto_id, costo_corrente, consumi_settimana):

        """Implementa la ricorsione"""
        if giorno>7:
            if self.__costo_ottimo == -1 or costo_corrente < self.__costo_ottimo:
                self.__costo_ottimo = costo_corrente
                self.__sequenza_ottima=list(sequenza_parziale)
            return
        if self.__costo_ottimo != -1 and costo_corrente >= self.__costo_ottimo:
            return

        for impianto in self._impianti:
            id_impianto_corrente=impianto.id
            costo=0
            if ultimo_impianto_id is not None and id_impianto_corrente!=ultimo_impianto_id:
                costo=5

            costo_consumo=consumi_settimana[id_impianto_corrente][giorno-1]
            nuovo_costo=costo_corrente+costo+costo_consumo
            sequenza_parziale.append(id_impianto_corrente)
            self.__ricorsione(sequenza_parziale,giorno+1,id_impianto_corrente,nuovo_costo,consumi_settimana)

            sequenza_parziale.pop()

    def __get_consumi_prima_settimana_mese(self, mese: int):
        """
        Restituisce i consumi dei primi 7 giorni del mese selezionato per ciascun impianto.
        :return: un dizionario: {id_impianto: [kwh_giorno1, ..., kwh_giorno7]}
        """
        consumi_settimana = {}

        for impianto in self._impianti:

            if impianto.lista_consumi is None:
                impianto.lista_consumi = ConsumoDAO.get_consumi(impianto.id)

            consumi_impianto = impianto.get_consumi()

            consumi_filtrati = []
            if consumi_impianto:
                for c in consumi_impianto:

                    if c.data.month == mese and (c.data.day>=1 and c.data.day <= 7):
                        consumi_filtrati.append(c)

            consumi_filtrati.sort(key=lambda x: x.data)
            kwh_settimana = [c.kwh for c in consumi_filtrati]
            consumi_settimana[impianto.id] = kwh_settimana

        return consumi_settimana
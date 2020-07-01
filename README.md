Spanish Below

# Lucas. The cryptocurrency helper

Lucas is a software made to manage my investments in cryptocurrencies.
It does not make operations! But it can tell you about how it is going on.

### Database
It configures a SQLite database for personal uses. It includes trades, funds and balances.
The database is configured to work with MXN.

###### The creds.json file
I'm using this structure to save the "sensitive" data, for obvious reasons I am not uploading these one.
```{
    "emiter": "your email notifier",
    "password": "its password", 
    "recievers": [emails you want to notify]
    }
``` 

### Alert
The alert uses the database's balances to compare with the current prices.
It has many parameters for this evaluation:
    1. Growth: Describes the quick growth from 1 window of time to another
    2. Dif: Describes changes according to your valuation
    3. Day: Changes in the rates greater than the "expected" in the day
    4. Custom: In case you want to be notified with custom prices

The first three are porcentual amounts, whereas custom are raw values.
I used an gmail adress as notification, but you can use sellenium or any other tool to configure yours.

# Lucas. El asistente de criptomendas

Lucas es un software hecho para tener control de inversiones en criptomonedas
No realiza operaciones, solamente notifica si hay algo conveniente.

### Base de Datos
Genera una bd en SQLite para almacenar operaciones, ingresos y balances.
La bd está hecha para trabajar con MXN, y almacena el valor MXN/USD en las operaciones.

###### The creds.json file
Estoy usando esta estructura para guardar datos sensibles, por obvias razones no lo subiré.
```{
    "emiter": "cuenta notificadora",
    "password": "password para ingresar", 
    "recievers": [lista de destinatarios]
    }
```

### Alerta
La alerta se vale de los balances y valuaciones almacenadas y los compara con los precios de ese momento.
Tiene 4 parámetros o detonantes:
    1. Growth: Describe cambios súbitos en el precio de la moneda.
    2. Dif: Cambios respecto a tu valuación.
    3. Day: Cambios de precio fuera de lo "esperado" con respecto al día.
    4. Custom: Alertas personalizadas con precios fijos

Para las primeras 3 alertas, los valores dentro del json son porcentuales, los custom son absolutos.
Alert utiliza una cuenta gmail para notificarme en caso de que estos límites se rebasen, puedes hacer lo mismo o bien, utilizar otra aproximación.

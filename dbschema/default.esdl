module default {
    type User {
        required property tid -> int64 {
        	constraint exclusive;
        }
        required property lang -> str {
            default := "es";
        }
    }
}

CREATE MIGRATION m1d7vsvghx434wiohio7xdqu3sm7ltooh2tmfqojcqcgvkmaiazibq
    ONTO initial
{
  CREATE TYPE default::User {
      CREATE REQUIRED PROPERTY lang -> std::str {
          SET default := 'es';
      };
      CREATE REQUIRED PROPERTY tid -> std::int64 {
          CREATE CONSTRAINT std::exclusive;
      };
  };
};
